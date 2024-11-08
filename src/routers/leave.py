from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
from src.core.utils import send_email_leave
from src.core.database import get_db
from src.core.authentication import roles_required
from src.models.personal import EmployeeOnboarding
from src.models.leave import LeaveCalendar
from src.core.authentication import get_current_employee, get_current_employee_roles
from src.schemas.leave import (
    EmployeeLeaveCreate,
    EmployeeLeaveUpdate,
    LeaveCalendarUpdate
)
from src.crud.leave import (
    create_employee_leave,
    update_employee_leave,
    delete_employee_leave,
    get_leave_by_employee_id,
    get_leave_by_id,
    get_employee_leave_by_month,
    get_leave_by_employee_team,
    get_leave_by_admin,
    get_leave_by_report_manager,
    update_employee_teamlead,
    get_employee_leave_by_month_tl,
    leave_calender,
    get_calender,
    get_calender_tl,
    update_leave_calendar
)

router = APIRouter(
    prefix="/leave", tags=["leave"], responses={400: {"message": "Not found"}}
)


@router.post(
    "/", dependencies=[Depends(roles_required("employee", "admin", "teamlead"))]
)
async def apply_leave(
    leave: EmployeeLeaveCreate,
    db: Session = Depends(get_db),
    current_employee=Depends(get_current_employee),  # Ensure this is the correct type
):
    # Accessing employee_id directly from the object
    employee_id = current_employee.employment_id
    if not employee_id:
        raise HTTPException(status_code=400, detail="Invalid employee data")
    db_leave = create_employee_leave(db, leave, employee_id)
    await send_email_leave(
        db_leave["employee_email"],
        db_leave["employee_firstname"],
        db_leave["employee_lastname"],
        db_leave["leave"],
        db_leave["reason"],
        db_leave["status"],
        db_leave["other_entires"],
    )
    return {"leave applied successfully check your mail"}


@router.get(
    "/details", dependencies=[Depends(roles_required("employee", "teamlead"))]
)
def get_leaves_by_employee( 
    db: Session = Depends(get_db),
    current_employee=Depends(get_current_employee),
):
    current_employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db).name
    
    # Determine employee to fetch leave details for
    if employee_role == "employee" or employee_role == "teamlead":
        db_employee = get_leave_by_employee_id(db, current_employee_id)
    else:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not applied for leave")

    return db_employee


@router.get(
    "/pending/leave",
    dependencies=[Depends(roles_required("employee", "teamlead"))],
)
def get_leave_by(
    db: Session = Depends(get_db), current_employee=Depends(get_current_employee)
):
    current_employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    if employee_role.name == "employee":
        db_leave = get_leave_by_id(db, current_employee_id)
    if employee_role.name == "teamlead":
        db_leave = get_leave_by_report_manager(db, current_employee_id)
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave_details = [
        {"employee_id": leave.employee.employee_id, "leave_id": leave.id}
        for leave in db_leave
    ]

    return leave_details


@router.get(
    "/{monthnumber}/{yearnumber}",
    dependencies=[Depends(roles_required("employee","teamlead"))],
)
def get_leave_by_month(
    monthnumber: int,
    yearnumber: int,
    db: Session = Depends(get_db),
    current_employee: EmployeeOnboarding = Depends(get_current_employee),
):
    current_employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    if employee_role.name == "employee":
        return get_employee_leave_by_month(db, current_employee_id, monthnumber, yearnumber)
    if employee_role.name == "teamlead":
            return get_employee_leave_by_month(db, current_employee_id, monthnumber, yearnumber)
    return {"detail": "No leaves this Month"}


@router.put("/admin/teamlead/update", dependencies=[Depends(roles_required("teamlead", "admin"))])
async def update_leave(
    leave: EmployeeLeaveUpdate,
    db: Session = Depends(get_db),
    current_employee=Depends(get_current_employee),
):
    report_manager = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    if employee_role.name == "admin":
        if leave.status == "approved":
            db_leave = update_employee_leave(db, leave)
        elif leave.status == "rejected":
            if not leave.reason or not leave.reason.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Please provide a reason for rejecting the leave.",
                )
            db_leave = update_employee_leave(db, leave)
        else:
            raise HTTPException(
                status_code=400, detail="Invalid leave status provided."
            )
    if employee_role.name == "teamlead":
        if leave.status == "approved":
            db_leave = update_employee_teamlead(db, report_manager, leave)
        elif leave.status == "rejected":
            if not leave.reason or not leave.reason.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Please provide a reason for rejecting the leave.",
                )
            db_leave = update_employee_teamlead(db, report_manager, leave)
        else:
            raise HTTPException(
                status_code=400, detail="Invalid leave status provided."
            )

    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    await send_email_leave(
        db_leave["employee_email"],
        db_leave["employee_firstname"],
        db_leave["employee_lastname"],
        db_leave["leave"],
        db_leave["reason"],
        db_leave["status"],
        db_leave["other_entires"],
    )
    return db_leave


@router.delete(
    "/{leave_id}",
    dependencies=[Depends(roles_required("employee", "teamlead"))],
)
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_employee),
):
    success = delete_employee_leave(db, current_user.id, leave_id)
    if not success:
        raise HTTPException(status_code=404, detail="Leave not found")
    return {"leave deleted successfully"}




@router.get("/calender", dependencies=[Depends(roles_required("employee","teamlead"))])
async def get_leave_calendar(db: Session = Depends(get_db),current_employee=Depends(get_current_employee)):
    employee_id=current_employee.id
    return get_calender(db,employee_id)

@router.get("/teamlead/calender/{employee_id}", dependencies=[Depends(roles_required("teamlead"))])
async def get_leave_calendar_tl(employee_id: str = Path(...),db: Session = Depends(get_db),current_employee=Depends(get_current_employee)):
    report_manager=current_employee.employment_id
    return get_calender_tl(db,report_manager,employee_id)


