from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.personal import EmployeeOnboarding
from src.models.employee import EmployeeEmploymentDetails
from src.schemas.personal import EmployeeCreate, EmployeeUpdate
from datetime import datetime
from src.models.role import Role
from sqlalchemy import insert


from src.core.utils import normalize_string, generate_password, hash_password
from src.models.association import employee_role


def create_employee(db: Session, employee: EmployeeCreate):

    exist_number = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.contactnumber == employee.contactnumber)
        .first()
    )
    exist_email = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.emailaddress == employee.emailaddress)
        .first()
    )
    if len(str(employee.contactnumber)) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact number  must be 10 numbers",
        )
    if exist_number or exist_email:
        raise HTTPException(
            status_code=status.HTTP_208_ALREADY_REPORTED,
            detail="Contact number or email address already exists",
        )

    new_details = EmployeeOnboarding(
        firstname=employee.firstname,
        lastname=employee.lastname,
        dateofbirth=employee.dateofbirth,
        contactnumber=employee.contactnumber,
        emailaddress=employee.emailaddress,
        address=employee.address,
        nationality=employee.nationality,
        gender=employee.gender,
        maritalstatus=employee.maritalstatus,
    )

    db.add(new_details)
    db.commit()
    db.refresh(new_details)

    new_details.employment_id = f"cds{str(new_details.id).zfill(4)}"
    email_address = f"{employee.firstname.lower()}{employee.lastname.lower()}{str(new_details.id)}@conversedatasolution.com"

    db.add(new_details)
    db.commit()
    password = generate_password()
    hashed_password = hash_password(password)
    email_upload = EmployeeEmploymentDetails(
        employee_email=email_address,
        password=hashed_password,
        job_position="Not Specified",
        department="Not Specified",
        start_date=datetime.utcnow(),
        employment_type="Not Specified",
        reporting_manager=0,
        work_location="Not Specified",
        basic_salary=0.0,
        releave_date=None,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        employee_id=new_details.employment_id,
    )
    db.add(email_upload)
    db.commit()
    role = db.query(Role).filter(Role.name == "employee").first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=" Default Role is not Found "
        )
    db_employee_role = (
        db.query(employee_role)
        .filter(
            employee_role.c.employee_id == new_details.id,
            employee_role.c.role_id == role.id,
        )
        .first()
    )
    if not db_employee_role:
        new_employee_role = {"employee_id": new_details.id, "role_id": role.id}
        insert_statement = insert(employee_role).values(new_employee_role)
        db.execute(insert_statement)
        db.commit()

    return {
        "emailaddress": new_details.emailaddress,
        "firstname": new_details.firstname,
        "lastname": new_details.lastname,
        "employee_email": email_upload.employee_email,
        "password": password,
    }


def get_employee(db: Session, employee_id: str):
    data=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.employment_id == employee_id).first()
    return data



def update_employee(db: Session, employee_id: str, update_data: EmployeeUpdate):
    # Fetch the employee record
    db_employee = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.employment_id == employee_id)
        .first()
    )
    if db_employee is None:
        return None

    if update_data.contactnumber is not None:
        exist_number = (
            db.query(EmployeeOnboarding)
            .filter(EmployeeOnboarding.contactnumber == update_data.contactnumber)
            .first()
        )
        if exist_number and exist_number.employment_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_208_ALREADY_REPORTED,
                detail="Contact number already exists",
            )

    if update_data.emailaddress is not None:
        exist_email = (
            db.query(EmployeeOnboarding)
            .filter(EmployeeOnboarding.emailaddress == update_data.emailaddress)
            .first()
        )
        if exist_email and exist_email.employment_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_208_ALREADY_REPORTED,
                detail="Email address already exists",
            )

    for key, value in update_data.dict(exclude_unset=True).items():
        if key in [
            "firstname",
            "lastname",
            "address",
            "nationality",
            "gender",
            "maritalstatus",
            "emailaddress",
        ]:
            setattr(db_employee, key, normalize_string(value))
        else:
            setattr(db_employee, key, value)
    
    db.commit()
    db.refresh(db_employee)
    return db_employee




# def delete_employee(db: Session, employee_id: str):

#     db_employee = (
#         db.query(EmployeeEmploymentDetails)
#         .filter(EmployeeEmploymentDetails.employee_id == employee_id)
#         .first()
#     )
    
#     if db_employee:
#         try:
            
#             # Mark employee as inactive
#             db_employee.is_active = False
            
#             # Commit the changes
#             db.commit()
            
#             # Refresh to get the updated data from the DB
#             db.refresh(db_employee)
            
#             return db_employee  # Return the updated employee record
#         except Exception as e:
#             db.rollback()  # Rollback in case of an error
#             raise HTTPException(status_code=500, detail=f"Error updating employee status: {str(e)}")
    
#     # If no employee is found, return a 404
#     raise HTTPException(status_code=404, detail="Employee not found")