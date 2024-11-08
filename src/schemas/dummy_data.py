from datetime import datetime, date
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    EmployeeOnboarding,
    EmployeeEmploymentDetails,
    Role,
    RoleFunction,
    employee_role,
)
from src.models.leave import EmployeeLeave, LeaveDuration, LeaveStatus
from src.core.utils import hash_password
from fastapi import FastAPI
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# Create a new engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Create metadata
metadata = MetaData()


def insert_dummy_data():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Insert roles
        # Dummy data for roles
    admin_role = Role(
        name="admin",
        sick_leave=10,
        personal_leave=5,
        vacation_leave=15
    )

    teamlead_role = Role(
        name="teamlead",
        sick_leave=8,
        personal_leave=4,
        vacation_leave=12
    )

    employee_role = Role(
        name="employee",
        sick_leave=6,
        personal_leave=3,
        vacation_leave=10
    )


    session.add_all([admin_role, teamlead_role, employee_role])
    session.commit()

    # Insert role functions
    admin_functions = [
    RoleFunction(
        role_id=admin_role.id,
        function="create personal detail",
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function="get personal detail",
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='update personal detail',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function="create new leave",
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='get employee detail',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='update employee detail',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='delete employee detail',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='create new role',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='get role',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='update role',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='delete role',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='create role function',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='get role function',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='delete role function',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='assign role to employee',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='get pending leaves',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='get leave history',
        jsonfile="admin.json",
    ),
    RoleFunction(
        role_id=admin_role.id,
        function='update leave status',
        jsonfile="admin.json",
    ),RoleFunction(
        role_id=admin_role.id,
        function='delete leave record',
        jsonfile="admin.json",
    ),RoleFunction(
        role_id=admin_role.id,
        function='create leave calender',
        jsonfile="admin.json",
    ),RoleFunction(
        role_id=admin_role.id,
        function='get leave calender',
        jsonfile="admin.json",
    ),RoleFunction(
        role_id=admin_role.id,
        function='update leave calender',
        jsonfile="admin.json",
    )]

    
    teamlead_functions = [
    RoleFunction(
        role_id=teamlead_role.id,
        function='update personal detail',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='Read employee detail',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='apply new leave',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='get pending leaves',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='get leave history',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='update leave status',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='delete leave record',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='get leave calender',
        jsonfile="teamlead.json",
    ),
    RoleFunction(
        role_id=teamlead_role.id,
        function='get employee leave calender',
        jsonfile="teamlead.json",
    )
]

    employee_functions = [
    RoleFunction(
        role_id=employee_role.id,
        function='update personal detail',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='Read employee detail',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='Apply Leave Request',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='get pending leaves',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='get leave history',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='delete leave record',
        jsonfile="employee.json",
    ),
    RoleFunction(
        role_id=employee_role.id,
        function='get leave calender',
        jsonfile="employee.json",
    )
]

    session.add_all(admin_functions + teamlead_functions + employee_functions)
    session.commit()

    # Insert employees
    admin_employee = EmployeeOnboarding(
        employment_id="cds0001",
        firstname="admin",
        lastname="admin",
        dateofbirth=date(1985, 7, 10),
        contactnumber=1112233445,
        emailaddress="hariprathap670@gmail.com",
        address="123 Admin St",
        nationality="American",
        gender="male",
        maritalstatus="Single",
    )

    teamlead_employee = EmployeeOnboarding(
        employment_id="cds0002",
        firstname="teamlead",
        lastname="tl",
        dateofbirth=date(1988, 3, 22),
        contactnumber=5556677889,
        emailaddress="kavin@gmail.com",
        address="456 Leader Rd",
        nationality="American",
        gender="Male",
        maritalstatus="Married",
    )

    regular_employee = EmployeeOnboarding(
        employment_id="cds0003",
        firstname="employee",
        lastname="emp",
        dateofbirth=date(1992, 11, 5),
        contactnumber=9998887770,
        emailaddress="employee@gmail.com",
        address="789 Worker Ave",
        nationality="American",
        gender="Non-Binary",
        maritalstatus="Single",
    )

    session.add_all([admin_employee, teamlead_employee, regular_employee])
    session.commit()

    # Insert employment details
    admin_password = hash_password("adminpass123")
    teamlead_password = hash_password("teamleadpass456")
    employee_password = hash_password("emppass789")

    admin_employment_details = EmployeeEmploymentDetails(
        employee_email="admin@conversedatasolution.com",
        password=admin_password,
        job_position="Administrator",
        department="Administration",
        start_date=date(2020, 1, 1),
        employment_type="Full-time",
        reporting_manager=None,
        work_location="Main Office",
        basic_salary=80000.00,
        employee_id=admin_employee.employment_id,  # Must match admin_employee.employment_id
    )

    teamlead_employment_details = EmployeeEmploymentDetails(
        employee_email="teamlead@conversedatasolution.com",
        password=teamlead_password,
        job_position="Team Leader",
        department="Engineering",
        start_date=date(2021, 6, 1),
        employment_type="Full-time",
        reporting_manager="cds0001",
        work_location="Main Office",
        basic_salary=75000.00,
        employee_id=teamlead_employee.employment_id,  # Must match teamlead_employee.employment_id
    )

    regular_employment_details = EmployeeEmploymentDetails(
        employee_email="employee@conversedatasolution.com",
        password=employee_password,
        job_position="Software Engineer",
        department="Engineering",
        start_date=date(2022, 3, 15),
        employment_type="Full-time",
        reporting_manager="cds0002",
        work_location="Main Office",
        basic_salary=70000.00,
        employee_id=regular_employee.employment_id,  # Must match regular_employee.employment_id
    )

    session.add_all(
        [
            admin_employment_details,
            teamlead_employment_details,
            regular_employment_details,
        ]
    )
    session.commit()

    # Insert roles
    employee_role_table = Table("employee_role", metadata, autoload_with=engine)

    session.execute(
        employee_role_table.insert().values(
            [
                {"employee_id": admin_employee.id, "role_id": admin_role.id},
                {"employee_id": teamlead_employee.id, "role_id": teamlead_role.id},
                {"employee_id": regular_employee.id, "role_id": employee_role.id},
            ]
        )
    )
    session.commit()

    # Insert leaves
    leaves = [
        EmployeeLeave(
            employee_id=admin_employee.id,
            leave_type="sick",
            duration=LeaveDuration.ONE_DAY,
            start_date=date(2024, 9, 10),
            end_date=date(2024, 9, 10),
            status=LeaveStatus.APPROVED,
            reason="Flu",
            reject_reason=None,
        ),
        EmployeeLeave(
            employee_id=teamlead_employee.id,
            leave_type="vacation",
            duration=LeaveDuration.HALF_DAY,
            start_date=date(2024, 9, 15),
            end_date=date(2024, 9, 15),
            status=LeaveStatus.PENDING,
            reason="Family Event",
            reject_reason=None,
        ),
        EmployeeLeave(
            employee_id=regular_employee.id,
            leave_type="personal",
            duration=LeaveDuration.ONE_DAY,
            start_date=date(2024, 9, 20),
            end_date=date(2024, 9, 20),
            status=LeaveStatus.REJECTED,
            reason="Urgent Personal Matter",
            reject_reason="Insufficient Leave Balance",
        ),
    ]

    session.add_all(leaves)
    session.commit()


if __name__ == "__main__":
    insert_dummy_data()
    print("Dummy data inserted successfully.")
