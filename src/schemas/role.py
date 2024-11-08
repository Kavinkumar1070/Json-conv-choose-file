from pydantic import BaseModel
from typing import Optional


class RoleCreate(BaseModel):
    name: str
    sick_leave: int
    personal_leave: int
    vacation_leave: int

    class Config:
        from_attributes = True


class UpdateRole(BaseModel):
    role_id: int
    new_name: str
    sick_leave: Optional[int] = None
    personal_leave: Optional[int] = None
    vacation_leave: Optional[int] = None


class EmployeeRole(BaseModel):
    employee_id: str
    role_id: int


class RoleFunctionCreate(BaseModel):
    role_id: int
    function: str
    jsonfile: str


class RoleFunctionUpdate(BaseModel):
    function: str | None = None
    jsonfile: str | None = None
