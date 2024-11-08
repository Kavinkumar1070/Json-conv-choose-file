from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class EmployeeEmploymentDetailsBase(BaseModel):
    employment_id: str
    job_position: str
    email:EmailStr
    password:str
    department: str
    start_date: date
    employment_type: str
    reporting_manager: Optional[str]
    work_location: Optional[str]
    basic_salary: Optional[float]


class EmployeeEmploymentDetailsCreate(EmployeeEmploymentDetailsBase):
    pass


class EmployeeEmploymentDetailsUpdate(BaseModel):
    employment_id: str = "cds0001"
    job_position: str | None = None
    department: str | None = None
    start_date: date | None = None
    employment_type: str | None = None
    reporting_manager: Optional[str] = None
    work_location: Optional[str] = None
    employee_email: Optional[EmailStr] = None
    basic_salary: Optional[float] = None


class EmployeeEmploymentDetails(EmployeeEmploymentDetailsBase):
    id: int
    employment_id: str

    class Config:
        orm_mode = True


class Login(BaseModel):
    email: str
    password: str
