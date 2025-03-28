from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import SessionLocal, Employee, Shipment, Attendance, Company, Task, OperationTaskMessage  # Ensure all models exist
import datetime
from typing import Optional

app = FastAPI()

# Print registered routes on startup
@app.on_event("startup")
def print_routes():
    print("Registered routes:")
    for route in app.routes:
        print(route.path)

# Root endpoint to verify the app is running
@app.get("/")
def read_root():
    return {"message": "App is running"}

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Endpoints for the application
# -----------------------------

# Login models
class LoginRequest(BaseModel):
    username: str
    password: str
    company_id: int

class LoginResponse(BaseModel):
    id: int
    name: str
    role: str
    company_id: int

@app.post("/login/", response_model=LoginResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter_by(username=login_req.username).first()
    if not user or not user.check_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid login credentials")
    if user.role != "owner" and user.company_id != login_req.company_id:
        raise HTTPException(status_code=401, detail="Invalid login credentials")
    return LoginResponse(
        id=user.id,
        name=user.name,
        role=user.role,
        company_id=user.company_id
    )

# Model for creating an employee
class EmployeeCreate(BaseModel):
    name: str
    username: str
    password: str

@app.post("/employees/")
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter_by(username=emp.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_emp = Employee(name=emp.name, username=emp.username, role="employee")
    new_emp.set_password(emp.password)
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return {"id": new_emp.id, "name": new_emp.name}

# Updated Shipment response model (for search)
class ShipmentResponse(BaseModel):
    id: int
    shipment_id: str
    status: str
    checked: bool
    imported: bool
    inspected_date: Optional[datetime.datetime] = None
    inspected_by: Optional[str] = None

    class Config:
        orm_mode = True

# Endpoint to search for a shipment by its shipment number.
# It returns shipment details along with the inspection date and inspector's name.
@app.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Retrieve inspector's name if shipment.inspected_by is set
    inspector_name = None
    if shipment.inspected_by:
        inspector = db.query(Employee).filter(Employee.id == shipment.inspected_by).first()
        if inspector:
            inspector_name = inspector.name

    return ShipmentResponse(
        id=shipment.id,
        shipment_id=shipment.shipment_id,
        status=shipment.status,
        checked=shipment.checked,
        imported=shipment.imported,
        inspected_date=shipment.inspected_date,
        inspected_by=inspector_name
    )

# Model for recording attendance (request)
class AttendanceRecord(BaseModel):
    employee_id: int
    check_type: str  # "check-in" or "check-out"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Model for attendance response (includes id and timestamp)
class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    check_type: str
    timestamp: datetime.datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        orm_mode = True

# Endpoint for recording attendance
@app.post("/attendance/", response_model=AttendanceResponse)
def record_attendance(record: AttendanceRecord, db: Session = Depends(get_db)):
    new_record = Attendance(
        employee_id=record.employee_id,
        check_type=record.check_type,
        timestamp=datetime.datetime.utcnow(),
        latitude=record.latitude,
        longitude=record.longitude
    )
    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording attendance: {e}")

# Model for company settings (if used)
class CompanySettings(BaseModel):
    company_id: int
    working_start: str
    working_end: str
    geo_latitude: float
    geo_longitude: float
    geo_radius: float
    company_address: Optional[str] = None

@app.post("/company/update_settings/")
def update_company_settings(settings: CompanySettings, db: Session = Depends(get_db)):
    company = db.query(Company).filter_by(id=settings.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.working_start = settings.working_start
    company.working_end = settings.working_end
    company.geo_latitude = settings.geo_latitude
    company.geo_longitude = settings.geo_longitude
    company.geo_radius = settings.geo_radius
    company.company_address = settings.company_address
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating settings: {e}")
    return {"detail": "Settings updated successfully"}

# Endpoint for creating tasks
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    created_by: int
    assigned_to: int

class TaskResponse(BaseModel):
    id: int
    title: str
    status: str

    class Config:
        orm_mode = True

@app.post("/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(title=task.title, description=task.description, created_by=task.created_by, assigned_to=task.assigned_to)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Endpoint for adding task messages
class TaskMessageCreate(BaseModel):
    task_id: int
    sender_id: int
    message: str

class TaskMessageResponse(BaseModel):
    id: int
    task_id: int
    sender_id: int
    message: str

    class Config:
        orm_mode = True

@app.post("/tasks/messages/", response_model=TaskMessageResponse)
def add_task_message(msg: TaskMessageCreate, db: Session = Depends(get_db)):
    new_msg = OperationTaskMessage(task_id=msg.task_id, sender_id=msg.sender_id, message=msg.message)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

# If you want to add more endpoints, do so here.
