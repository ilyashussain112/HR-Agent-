# main.py
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlmodel import SQLModel, Field, Session, create_engine, select
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory "database"
employees = {
    101: {"name": "Ali", "department": "IT"},
    102: {"name": "Sara", "department": "HR"}
}

leave_requests = {}  # leave records store karne ke liye
leave_counter = 1

class LeaveRequest(BaseModel):
    employee_id: int
    start_date: str
    end_date: str
    leave_type: str
    reason: str

@app.post("/leave")
def request_leave(req: LeaveRequest):
    global leave_counter

    # Check if employee exists
    if req.employee_id not in employees:
        raise HTTPException(status_code=404, detail="Employee not found")

    leave_id = leave_counter
    leave_requests[leave_id] = {
        "employee_id": req.employee_id,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "leave_type": req.leave_type,
        "reason": req.reason,
        "status": "Pending"
    }
    leave_counter += 1

    return {
        "leave_id": leave_id,
        "status": "Pending",
        "message": "Leave request submitted"
    }


app = FastAPI(title="HR Agent - Leave MVP Prototype")

# -----------------------
# Database models
# -----------------------
class Employee(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    manager_id: Optional[str] = None
    leave_balance: int = 10  # days
    manager_auto_approve: bool = False

class LeaveRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    employee_id: str
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str] = None
    status: str = "submitted"  # submitted / pending / approved / rejected / cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    manager_id: Optional[str] = None
    policy_evidence: Optional[str] = None  # which policy snippet was used
    notes: Optional[str] = None

class AuditLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    leave_id: Optional[str] = None
    actor: str  # agent name or user id
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    detail: Optional[str] = None

class Notification(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    to: str
    message: str
    ts: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = False

# -----------------------
# Simple "policy corpus" for RAG-like lookup
# -----------------------
POLICY_SNIPPETS = [
    {"id": "L-ANNUAL-1", "title": "Annual Leave Eligibility",
     "text": "Annual leave is accrued monthly. Employees can take annual leave if balance >= requested days."},
    {"id": "L-BLACKOUT-1", "title": "Blackout Dates",
     "text": "Blackout period: 2025-12-20 to 2025-12-31. Leaves during blackout require manager approval."},
    {"id": "L-SICK-1", "title": "Sick Leave",
     "text": "Sick leave requires a medical certificate for 3 or more consecutive days."}
]

# -----------------------
# DB init (SQLite)
# -----------------------
sqlite_file_name = "hr_agent.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=False)
SQLModel.metadata.create_all(engine)

def seed_if_empty():
    with Session(engine) as session:
        stmt = select(Employee)
        existing = session.exec(stmt).first()
        if existing:
            return
        # Create sample manager and employees
        mgr = Employee(id="mgr-1", name="Alice Manager", manager_auto_approve=False)
        emp = Employee(id="emp-1", name="Ilyas Developer", manager_id=mgr.id, leave_balance=8)
        emp2 = Employee(id="emp-2", name="Sara Employee", manager_id=mgr.id, leave_balance=2, manager_auto_approve=True)
        session.add_all([mgr, emp, emp2])
        session.commit()

seed_if_empty()

# -----------------------
# Utility helpers
# -----------------------
def days_between(start: date, end: date) -> int:
    return (end - start).days + 1

def find_policy_evidence(query_text: str) -> Optional[dict]:
    # VERY simple keyword matching for demo. In prod use vector DB + RAG.
    q = query_text.lower()
    best = None
    for p in POLICY_SNIPPETS:
        if any(k in p["text"].lower() for k in q.split()):
            best = p
            break
    # fallback: return blackout if dates overlap
    return best

def create_audit(session: Session, leave_id: str, actor: str, action: str, detail: Optional[str]=None):
    al = AuditLog(leave_id=leave_id, actor=actor, action=action, detail=detail)
    session.add(al)
    session.commit()

def notify(session: Session, to: str, message: str):
    n = Notification(to=to, message=message)
    session.add(n)
    session.commit()
    print(f"[NOTIFY] to={to} msg='{message}'")  # simulate sending

BLACKOUTS = [(date(2025,12,20), date(2025,12,31))]

def overlaps_blackout(start: date, end: date) -> bool:
    for a, b in BLACKOUTS:
        if start <= b and end >= a:
            return True
    return False

# -----------------------
# Pydantic input models
# -----------------------
class LeaveIn(BaseModel):
    employee_id: str
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str] = None

class ApproveIn(BaseModel):
    manager_id: str
    approve: bool
    note: Optional[str] = None

# -----------------------
# Endpoints
# -----------------------

@app.post("/leave", response_model=dict)
def submit_leave(payload: LeaveIn):
    with Session(engine) as session:
        emp = session.get(Employee, payload.employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        # basic sanity
        if payload.end_date < payload.start_date:
            raise HTTPException(status_code=400, detail="end_date must be >= start_date")

        leave_days = days_between(payload.start_date, payload.end_date)
        leave = LeaveRequest(
            employee_id=emp.id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            leave_type=payload.leave_type,
            reason=payload.reason,
            manager_id=emp.manager_id
        )
        session.add(leave)
        session.commit()

        # Policy lookup (simple)
        qtext = f"{payload.leave_type} {payload.reason or ''}"
        evidence = find_policy_evidence(qtext)
        evidence_id = evidence["id"] if evidence else None
        leave.policy_evidence = evidence_id
        session.add(leave)
        session.commit()

        # Create audit: intake agent
        create_audit(session, leave.id, actor="IntakeAgent", action="submitted",
                     detail=f"days={leave_days} balance_before={emp.leave_balance}")

        # Validation and auto-approve logic
        conflicts = []
        if overlaps_blackout(payload.start_date, payload.end_date):
            conflicts.append("blackout_period")

        if leave_days <= emp.leave_balance and emp.manager_auto_approve and not conflicts:
            # auto-approve
            leave.status = "approved"
            leave.resolved_at = datetime.utcnow()
            session.add(leave)
            # deduct balance
            emp.leave_balance -= leave_days
            session.add(emp)
            session.commit()
            create_audit(session, leave.id, actor="HRAgent", action="auto_approved",
                         detail=f"auto-approve rule applied; days={leave_days}")
            notify(session, to=emp.id, message=f"Your leave {leave.id} has been auto-approved.")
            return {"status": "approved", "leave_id": leave.id, "policy_evidence": evidence_id}
        else:
            # route to manager
            leave.status = "pending"
            session.add(leave)
            session.commit()
            create_audit(session, leave.id, actor="HRAgent", action="routed_to_manager",
                         detail=f"conflicts={conflicts} days={leave_days} balance={emp.leave_balance}")
            if emp.manager_id:
                notify(session, to=emp.manager_id, message=f"Leave {leave.id} pending approval for {emp.name}.")
            notify(session, to=emp.id, message=f"Your leave {leave.id} is pending manager approval.")
            return {"status": "pending", "leave_id": leave.id, "policy_evidence": evidence_id, "conflicts": conflicts}

@app.get("/leave/{leave_id}", response_model=dict)
def get_leave(leave_id: str):
    with Session(engine) as session:
        leave = session.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave not found")
        return {
            "id": leave.id,
            "employee_id": leave.employee_id,
            "start_date": str(leave.start_date),
            "end_date": str(leave.end_date),
            "status": leave.status,
            "policy_evidence": leave.policy_evidence,
            "notes": leave.notes
        }

@app.get("/manager/{mgr_id}/pending", response_model=List[dict])
def manager_pending(mgr_id: str):
    with Session(engine) as session:
        stmt = select(LeaveRequest).where(LeaveRequest.manager_id == mgr_id, LeaveRequest.status == "pending")
        rows = session.exec(stmt).all()
        return [{"id": r.id, "employee_id": r.employee_id, "start": str(r.start_date), "end": str(r.end_date)} for r in rows]

@app.post("/leave/{leave_id}/approve", response_model=dict)
def approve_leave(leave_id: str, payload: ApproveIn):
    with Session(engine) as session:
        leave = session.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave not found")
        if leave.manager_id != payload.manager_id:
            raise HTTPException(status_code=403, detail="Not authorized manager for this leave")

        emp = session.get(Employee, leave.employee_id)
        leave_days = days_between(leave.start_date, leave.end_date)

        if payload.approve:
            # check balance again (race conditions in real prod)
            if leave_days > emp.leave_balance:
                # can't approve if not enough balance
                leave.status = "rejected"
                leave.resolved_at = datetime.utcnow()
                leave.notes = "Insufficient balance"
                session.add(leave)
                session.commit()
                create_audit(session, leave.id, actor=payload.manager_id, action="rejected", detail="insufficient_balance")
                notify(session, to=emp.id, message=f"Your leave {leave.id} was rejected: insufficient balance.")
                return {"status": "rejected", "reason": "insufficient_balance"}
            leave.status = "approved"
            leave.resolved_at = datetime.utcnow()
            session.add(leave)
            emp.leave_balance -= leave_days
            session.add(emp)
            session.commit()
            create_audit(session, leave.id, actor=payload.manager_id, action="approved", detail=payload.note)
            notify(session, to=emp.id, message=f"Your leave {leave.id} was approved by manager.")
            return {"status": "approved"}
        else:
            leave.status = "rejected"
            leave.resolved_at = datetime.utcnow()
            leave.notes = payload.note
            session.add(leave)
            session.commit()
            create_audit(session, leave.id, actor=payload.manager_id, action="rejected", detail=payload.note)
            notify(session, to=emp.id, message=f"Your leave {leave.id} was rejected: {payload.note or 'no reason given'}")
            return {"status": "rejected"}

@app.get("/policy")
def policy_search(q: str):
    p = find_policy_evidence(q)
    if not p:
        return {"found": False, "message": "No direct policy snippet matched. Consider contacting HR."}
    return {"found": True, "policy_id": p["id"], "title": p["title"], "text": p["text"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
