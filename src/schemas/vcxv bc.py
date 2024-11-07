from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from src.core.database import get_db
from src.core.utils import verify_password,hash_password
from src.schemas.authentication import TokenData,ChangePassword
from src.models.personal import EmployeeOnboarding
from src.models.role import Role, RoleFunction
from src.models.association import employee_role
from src.models.employee import EmployeeEmploymentDetails

# Load environment variables from .env file
load_dotenv()

router = APIRouter()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_employee(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authentication": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: int = payload.get("sub")
        expires: datetime = payload.get("exp")
        # check
        if datetime.fromtimestamp(expires) < datetime.utcnow():
            return None
        if employee_id is None:
            raise credentials_exception
        token_data = TokenData(employee_id=employee_id)
    except JWTError:
        raise credentials_exception

    employee = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.id == token_data.employee_id)
        .first()
    )
    if employee is None:
        raise credentials_exception
    return employee


def get_current_user_function(
    db: Session,
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authentication": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: int = payload.get("sub")
        expires: datetime = payload.get("exp")
        # check
        if datetime.fromtimestamp(expires) < datetime.utcnow():
            return None
        if employee_id is None:
            raise credentials_exception
        token_data = TokenData(employee_id=employee_id)
    except JWTError:
        raise credentials_exception

    employee = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.id == token_data.employee_id)
        .first()
    )
    role = get_current_employee_roles(employee.id, db)
    role_functions = (
        db.query(RoleFunction).filter(RoleFunction.role_id == role.id).all()
    )
    role_function = [role_function.function for role_function in role_functions]
    role_file = [role_function.jsonfile for role_function in role_functions]
    return {
        "Employee_ID": employee.employment_id,
        "Role": role.name,
        "Functions": role_function,
        "file": role_file,
    }


def authenticate_employee(db: Session, employee_email: str, password: str):
    employee = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_email == employee_email)
        .first()
    )
    
    if not employee:
        return None
    if not verify_password(password, employee.password):
        return None

    return employee


def get_current_user_roles(
    current_user: EmployeeOnboarding = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> list:
    roles = (
        db.query(Role)
        .join(employee_role)
        .filter(employee_role.c.employee_id == current_user.id)
        .all()
    )
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have any assigned roles",
        )
    return [role.name for role in roles]


def get_current_employee_roles(
    current_user: int, db: Session = Depends(get_db)
) -> list:
    roles = (
        db.query(Role)
        .join(employee_role)
        .filter(employee_role.c.employee_id == current_user)
        .first()
    )
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have any assigned roles",
        )
    return roles


def roles_required(*required_roles: str):
    def role_dependency(user_roles: list = Depends(get_current_user_roles)):
        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for the current user's roles",
            )

    return role_dependency


def get_role_functions_by_role_id(db: Session, role_id: int):
    role_functions = (
        db.query(RoleFunction).filter(RoleFunction.role_id == role_id).all()
    )
    if not role_functions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No functions found for the given role ID",
        )

    return role_functions


@router.post("/token")
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    employee = authenticate_employee(db, form_data.username, form_data.password)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(employee.id), "exp": access_token_expires}
    )
    role = get_current_employee_roles(employee.id, db)
    role_functions = (
        db.query(RoleFunction).filter(RoleFunction.role_id == role.id).all()
    )
    role_function = [role_function.function for role_function in role_functions]
    role_file = [role_function.jsonfile for role_function in role_functions]
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role.name,
        "Functions": role_function,
        "file": role_file,
    }

def change_password(db:Session,hash_password_new:str,employee_id:int):
    print("sdsd",employee_id)
    print("asdf",hash_password_new)
    employee=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.id == employee_id).first()
    print(employee.id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Employee not Found")
    employee.password = hash_password_new
    db.add(employee)
    db.commit()
    return {"details":"Password Changed Successfully"}



@router.put("/change-password", dependencies=[Depends(roles_required("employee","teamlead","admin"))])
def change_password_with_old(data:ChangePassword,db:Session=Depends(get_db),current_employee=Depends(get_current_employee)):
    employee_id=current_employee.id
    employee=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.id == employee_id).first()
    verify=verify_password(data.current_password,employee.password)
    if not verify:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Current Password is Wrong ")
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="New Password  and Confirm Password is Mismatch")
    hash_new_password=hash_password(data.new_password)
    return change_password(db,hash_new_password,employee_id)

    # change_password

@router.get("/admin-endpoint", dependencies=[Depends(roles_required("admin"))])
def read_employee_me(
    current_employee: EmployeeOnboarding = Depends(get_current_employee),
):
    return current_employee
