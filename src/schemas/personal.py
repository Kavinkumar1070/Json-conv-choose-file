from pydantic import BaseModel, validator, ValidationError, Field, EmailStr
from dateutil import parser
from typing import Optional
from datetime import date


class EmployeeBase(BaseModel):
    firstname: str
    lastname: str
    dateofbirth: str 
    contactnumber: int
    emailaddress: EmailStr
    address: str
    nationality: str
    gender: str
    maritalstatus: str

    @validator("contactNumber", check_fields=False)
    def validate_phone_number(cls, value):
        contact_number_str = str(value)
        if not (10 == len(contact_number_str)):
            raise ValueError(
                "Invalid phone number length. Phone number must be between 9 and 12 digits."
            )
        return value

    @validator('dateofbirth', pre=True)
    def parse_date(cls, value):
        try:
            # Parse the date from various formats
            parsed_date = parser.parse(value)
            return parsed_date.strftime('%Y-%m-%d')  # Convert to standard format YYYY-MM-DD
        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Please use a valid date string.")

class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    dateofbirth: Optional[str] = Field(None, example="1990-05-15")
    contactnumber: Optional[int] = None
    emailaddress: Optional[EmailStr] = None
    address: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[str] = None
    maritalstatus: Optional[str] = None

    @validator("contactnumber", check_fields=False)
    def validate_phone_number(cls, value):
        if value is None:
            return value  # Skip validation if the value is None
    @validator('dateofbirth', pre=True)
    def parse_date(cls, value):
        if value is not None:
            try:
                # Parse the date from various formats
                parsed_date = parser.parse(value)
                return parsed_date.strftime('%Y-%m-%d')  # Convert to standard format YYYY-MM-DD
            except (ValueError, TypeError):
                raise ValueError("Invalid date format. Please use a valid date string.")
        return value

