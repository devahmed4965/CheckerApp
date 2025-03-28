from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import SessionLocal, Employee, Shipment, Attendance  # تأكد من أن Attendance معرف في models.py
import datetime
from typing import Optional


app = FastAPI()

# عند بدء التشغيل، نطبع قائمة المسارات للتأكد من تحميلها
@app.on_event("startup")
def print_routes():
    print("Registered routes:")
    for route in app.routes:
        print(route.path)

# نقطة النهاية الجذرية للتأكد من تشغيل التطبيق
@app.get("/")
def read_root():
    return {"message": "App is running"}

# دالة الاعتماد لإدارة جلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# نقاط النهاية الخاصة بالتطبيق
# -----------------------------

# نموذج بيانات تسجيل الدخول
class LoginRequest(BaseModel):
    username: str
    password: str
    company_id: int

class LoginResponse(BaseModel):
    id: int
    name: str
    role: str
    company_id: int

# نقطة نهاية تسجيل الدخول
@app.post("/login/", response_model=LoginResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter_by(username=login_req.username).first()
    if not user or not user.check_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid login credentials")
    # التحقق من معرّف الشركة في حالة عدم كون المستخدم مالكًا
    if user.role != "owner" and user.company_id != login_req.company_id:
        raise HTTPException(status_code=401, detail="Invalid login credentials")
    return LoginResponse(
        id=user.id,
        name=user.name,
        role=user.role,
        company_id=user.company_id
    )

# نموذج بيانات إنشاء موظف جديد
class EmployeeCreate(BaseModel):
    name: str
    username: str
    password: str

# نقطة نهاية إنشاء موظف جديد
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

# نقطة نهاية البحث عن شحنة بواسطة رقم الشحنة
@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {
        "id": shipment.id,
        "shipment_id": shipment.shipment_id,
        "status": shipment.status,
        "checked": shipment.checked,
        "imported": shipment.imported
    }

# نموذج بيانات تسجيل الحضور والانصراف
class AttendanceRecord(BaseModel):
    employee_id: int
    check_type: str  # "check-in" أو "check-out"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# نقطة نهاية تسجيل الحضور / الانصراف
@app.post("/attendance/", response_model=AttendanceRecord)
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
        return {
            "employee_id": new_record.employee_id,
            "check_type": new_record.check_type,
            "latitude": new_record.latitude,
            "longitude": new_record.longitude,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording attendance: {e}")
