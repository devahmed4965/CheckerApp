import os
import logging
import bcrypt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
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
    # Existing field for version URL
    version_url = Column(String(255), nullable=True)
    # New fields for Excel settings
    excel_id_column = Column(String(255), nullable=True)
    excel_status_column = Column(String(255), nullable=True)
    excel_line_statuses = Column(String(255), nullable=True)
    excel_return_statuses = Column(String(255), nullable=True)

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

# Update your DB credentials here:
DATABASE_URL = (
    "postgresql://shipping_owner:npg_Lnh9UCZP1bFT@ep-bold-forest-a5ejc2qg-pooler.us-east-2.aws.neon.tech/shipping?sslmode=require"
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
