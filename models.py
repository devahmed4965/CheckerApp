import os
import logging
import bcrypt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(255), unique=True, nullable=False)
    # Field for version URL
    version_url = Column(String(255), nullable=True)
    # New fields for Excel settings
    excel_id_column = Column(String(255), nullable=True)
    excel_status_column = Column(String(255), nullable=True)
    excel_line_statuses = Column(String(255), nullable=True)
    excel_return_statuses = Column(String(255), nullable=True)
    # Fields for working time and geographic boundaries
    working_start = Column(String(10), nullable=True)   # مثال "08:00"
    working_end = Column(String(10), nullable=True)     # مثال "17:00"
    geo_latitude = Column(Float, nullable=True)         # خط العرض
    geo_longitude = Column(Float, nullable=True)        # خط الطول
    geo_radius = Column(Float, nullable=True)           # نصف قطر النطاق (بالمتر)

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # Plain-text password (for demo only – not recommended in production)
    password_plain = Column(String(255), nullable=True)
    role = Column(String(50), default='employee', nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company = relationship('Company', backref='employees')

    def set_password(self, password):
        self.password_plain = password
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Shipment(Base):
    __tablename__ = 'shipments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(255), nullable=False)  # duplicates allowed
    status = Column(String(50), nullable=False)
    checked = Column(Boolean, default=False)
    imported = Column(Boolean, default=False)
    # The employee who owns the shipment
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    employee = relationship('Employee', foreign_keys=[employee_id], backref='shipments')
    inspected_date = Column(DateTime, nullable=True)
    # The employee who inspected the shipment
    inspected_by = Column(Integer, ForeignKey('employees.id'), nullable=True)
    inspector = relationship('Employee', foreign_keys=[inspected_by])

class EmployeeActivity(Base):
    __tablename__ = 'employee_activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    sheet_name = Column(String(255), nullable=False)
    shipment_count = Column(Integer, nullable=False)
    employee = relationship('Employee', backref='activities')

class UnmatchedShipment(Base):
    __tablename__ = 'unmatched_shipments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.datetime.now)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    employee = relationship('Employee', backref='unmatched_shipments')

# ----- النماذج الجديدة -----

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    created_by = Column(Integer, ForeignKey('employees.id'))
    assigned_to = Column(Integer, ForeignKey('employees.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("Employee", foreign_keys=[created_by], backref="created_tasks")
    assignee = relationship("Employee", foreign_keys=[assigned_to], backref="tasks")

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    check_type = Column(String(50), nullable=False)  # "check-in" أو "check-out"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    employee = relationship("Employee", backref="attendances")

# ----- نماذج مهام الأوبريشن -----

class OperationTask(Base):
    __tablename__ = 'operation_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    created_by = Column(Integer, ForeignKey('employees.id'))
    assigned_to = Column(Integer, ForeignKey('employees.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("Employee", foreign_keys=[created_by], backref="created_operation_tasks")
    assignee = relationship("Employee", foreign_keys=[assigned_to], backref="operation_tasks")

class OperationTaskMessage(Base):
    __tablename__ = 'operation_task_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('operation_tasks.id'))
    sender_id = Column(Integer, ForeignKey('employees.id'))
    message = Column(String(1024), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("OperationTask", backref="messages")
    sender = relationship("Employee")

# -----------------------------

# Update your DB credentials here:
DATABASE_URL = (
    "postgresql://shipping_owner:npg_y3r8BYRqNhWv@ep-flat-bonus-a5e6kv6t-pooler.us-east-2.aws.neon.tech/shipping?sslmode=require"
)

try:
    engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except OperationalError as e:
    logging.error("Error connecting to the database: %s", e)
    raise

def create_tables():
    try:
        Base.metadata.create_all(engine)
    except OperationalError as e:
        logging.error("Could not create tables (database offline?): %s", e)

if __name__ == "__main__":
    create_tables()
