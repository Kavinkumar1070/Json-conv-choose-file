from sqlalchemy.orm import Session
from src.models.employee import EmployeeEmploymentDetails
from src.models.personal import EmployeeOnboarding
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from src.core.authentication import get_current_employee_roles
from sqlalchemy.exc import SQLAlchemyError
from src.core.utils import normalize_string
from src.schemas.employee import (
    EmployeeEmploymentDetailsBase,
    EmployeeEmploymentDetailsUpdate,
    Login,
)
from src.models.association import employee_role


def create_employee_employment_details(
    db: Session, employee_employment_data: EmployeeEmploymentDetailsBase
):
    try:
        # Check if the employee already exists based on employee_id or employee_email
        existing_employee = db.query(EmployeeEmploymentDetails).filter(
            (EmployeeEmploymentDetails.employee_id == employee_employment_data.employment_id) |
            (EmployeeEmploymentDetails.employee_email == employee_employment_data.email)
        ).first()

        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with the given employee_id or email already exists."
            )

        # Validate EmployeeOnboarding record exists
        employee_onboarding = (
            db.query(EmployeeOnboarding)
            .filter(EmployeeOnboarding.employment_id == employee_employment_data.employment_id)
            .first()
        )
        if not employee_onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No EmployeeOnboarding record found for id {employee_employment_data.employment_id}"
            )

        # Validate reporting_manager exists and has a role
        reporting_manager = (
            db.query(EmployeeOnboarding)
            .filter(EmployeeOnboarding.employment_id == employee_employment_data.reporting_manager)
            .first()
        )
        if not reporting_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No EmployeeOnboarding record found for reporting manager {employee_employment_data.reporting_manager}"
            )

        # Validate that reporting manager has an associated role
        inter_data = (
            db.query(employee_role)
            .filter(employee_role.c.employee_id == reporting_manager.id)
            .first()
        )
        if not inter_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting manager is not associated with a role."
            )

        # Create new employee employment details
        new_employment_details = EmployeeEmploymentDetails(
            job_position=employee_employment_data.job_position,
            employee_email=employee_employment_data.email,
            password=employee_employment_data.password,
            department=employee_employment_data.department,
            start_date=employee_employment_data.start_date,
            employment_type=employee_employment_data.employment_type,
            reporting_manager=employee_employment_data.reporting_manager,
            work_location=employee_employment_data.work_location,
            basic_salary=employee_employment_data.basic_salary,
            is_active=True,
            employee_id=employee_employment_data.employment_id,
        )

        db.add(new_employment_details)
        db.commit()
        db.refresh(new_employment_details)
        return new_employment_details

    except SQLAlchemyError:
        db.rollback()
        raise
    except ValueError:
        raise



def get_all_employee_employment_details(db: Session, employee_id: str):
    emp = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    return emp


def get_all_employee_teamlead(db: Session, employee_id: str, reporting_manager: str):
    db_employee = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == employee_id,
            EmployeeEmploymentDetails.reporting_manager == reporting_manager,
        )
        .first()
    )
    if not db_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Can Not Access Employee Details")
    return db_employee

def update_employee_employment_details(
    db: Session, updates: EmployeeEmploymentDetailsUpdate
):
    # Fetch the employee employment details by employee_id
    employee_employment = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == updates.employment_id)
        .first()
    )
    
    if not employee_employment:
        # Return None or raise an exception if the employee is not found
        return None

    # If reporting_manager is provided in the update payload
    if updates.reporting_manager:
        # Fetch the reporting manager details
        reporting_manager = (
            db.query(EmployeeOnboarding)
            .filter(EmployeeOnboarding.employment_id == updates.reporting_manager)
            .first()
        ) 
        role=get_current_employee_roles(reporting_manager.id,db)
        if not role.name == "teamlead" and not role.name == "admin":
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting_manager is not associated with role",
            )

        # If no reporting manager is found, raise an HTTP exception
        if not reporting_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting_manager id should not be empty or was not found",
            )

        # Check if the reporting manager is associated with a role
        inter_data = (
            db.query(employee_role)
            .filter(employee_role.c.employee_id == reporting_manager.id)
            .first()
        )

        if not inter_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting manager is not associated with a role",
            )
        
        # Update the employee employment record with the reporting manager
        employee_employment.reporting_manager = reporting_manager.employment_id

    # Loop through all the fields in the updates that are set (exclude unset)
    for key, value in updates.dict(exclude_unset=True).items():
        # Normalize specific string fields if present in the update payload
        if key in ["job_position", "department", "work_location", "employee_email"]:
            setattr(employee_employment, key, normalize_string(value))
        # Convert basic_salary to float if it’s not None
        elif key == "basic_salary" and value is not None:
            setattr(employee_employment, key, float(value))
        # Check for a valid start_date and apply
        elif key == "start_date" and isinstance(value, date):
            setattr(employee_employment, key, value)
        # Set other fields directly
        else:
            setattr(employee_employment, key, value)

    # Ensure the employee is marked as active
    employee_employment.is_active = True

    # Commit the transaction to persist the changes in the database
    db.commit()

    # Refresh the employee employment object to get the updated state
    db.refresh(employee_employment)

    # Return the updated employee employment details
    return employee_employment


def delete_employee_employment_details(db: Session, employee_id: str):
    employee_employment = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    if employee_employment:
        employee_employment.is_active = False
        db.commit()
    return employee_employment


