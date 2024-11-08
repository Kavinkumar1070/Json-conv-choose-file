from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.utils import normalize_string
from src.core.authentication import roles_required,get_current_employee,get_current_employee_roles
from src.core.database import get_db

from src.crud.role import *
from src.schemas.role import RoleFunctionCreate

from src.schemas.role import (
    UpdateRole,
    RoleCreate,
    EmployeeRole,
)

router = APIRouter(
    prefix="/admin/roles", tags=["admin/role"], responses={400: {"message": "Not found"}}
)


@router.post("", dependencies=[Depends(roles_required("admin"))])
async def create_role(name: RoleCreate, db: Session = Depends(get_db)):
    name.name = normalize_string(name.name)
    if create(db, name):
        return f"{name} Role Created Successfully"
    return {"message": f"{name} Role is Already Exists"}


@router.delete("/{role_id}", dependencies=[Depends(roles_required("admin"))])
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = get_single(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return delete(db, role.id)


@router.put("/", dependencies=[Depends(roles_required("admin"))])
async def update_role(request: UpdateRole, db: Session = Depends(get_db)):
    exists_role = get_single(db, request.role_id)
    if exists_role:
        update(db,request)
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Role updated")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found"
        )


@router.get("/", dependencies=[Depends(roles_required("admin"))])
async def get_roles( db: Session = Depends(get_db)):
    role = get(db)
    return role


@router.post("/employee/role", dependencies=[Depends(roles_required("admin"))])
def assign_role_to_employee(data: EmployeeRole, db: Session = Depends(get_db)):
    data = assign_employee_role(db, data)
    if data:
        return data


# RoleFunction endpoints
@router.post("/functions/", dependencies=[Depends(roles_required("admin"))])
def create_new_role_function(
    role_function: RoleFunctionCreate, db: Session = Depends(get_db)
):
    return create_role_function(db, role_function)


@router.get("/{role_id}/functions/", dependencies=[Depends(roles_required("admin"))])
def read_role_functions(role_id: int, db: Session = Depends(get_db),current_employee=Depends(get_current_employee)):
    employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    print(employee_id)
    if employee_role.name == "admin":
        return get_role_functions(db, role_id)


@router.delete("/functions/{id}", dependencies=[Depends(roles_required("admin"))])
def delete_existing_role_function(id: int, db: Session = Depends(get_db)):
    db_role_function = delete_role_function(db, id)
    if db_role_function is None:
        raise HTTPException(status_code=404, detail="Role Function not found")
    return db_role_function
