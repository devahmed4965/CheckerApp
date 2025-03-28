import sys
import threading
import logging
import json
import os
import PIL.Image  # Pillow required to work with images
import webbrowser
from tkinter import messagebox
import customtkinter as ctk

# Import database models and settings
from models import SessionLocal, Employee, Company, Shipment, create_tables, Attendance, OperationTask, OperationTaskMessage
from sqlalchemy.exc import OperationalError

# --- Global login settings ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cached employees list
employees = []
OFFLINE_EMP_CACHE = "offline_employees_cache.json"
APP_NAME = "البوصلة"  # Application name

# Version info
CURRENT_VERSION = "1.0.0"
LATEST_VERSION = "1.1.0"

def cache_employees(employees_list):
    """
    Save employees locally for offline use.
    """
    data = []
    for emp in employees_list:
        data.append({
            "name": emp.name,
            "username": emp.username,
            "role": emp.role,
            "company_id": emp.company_id,
            # For testing: default password is stored (in production, store only hashes)
            "password": "Ahmed49654965@@"
        })
    try:
        if os.access(os.path.dirname(OFFLINE_EMP_CACHE) or '.', os.W_OK):
            with open(OFFLINE_EMP_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            logging.error("Cannot write to cache file: Permission denied")
    except Exception as e:
        logging.error("Error caching employees: %s", e)

def load_offline_employees():
    """
    Load employees from a local JSON file.
    """
    employees_list = []
    try:
        if not os.path.exists(OFFLINE_EMP_CACHE):
            logging.warning("Offline cache file not found")
            default_emp = Employee(name="Offline Owner", username="owner", role="owner", company_id=1)
            default_emp.set_password("Ahmed49654965@@")
            return [default_emp]
        with open(OFFLINE_EMP_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for d in data:
                emp = Employee(
                    name=d.get("name", "Offline User"),
                    username=d.get("username", "owner"),
                    role=d.get("role", "owner"),
                    company_id=d.get("company_id", 1)
                )
                emp.set_password(d.get("password", "Ahmed49654965@@"))
                employees_list.append(emp)
        return employees_list
    except Exception as e:
        logging.error("Error loading offline employees: %s", e)
        default_emp = Employee(name="Offline Owner", username="owner", role="owner", company_id=1)
        default_emp.set_password("Ahmed49654965@@")
        return [default_emp]

def initialize_database():
    """
    Create tables, default data, and retrieve employees.
    """
    try:
        create_tables()

        session = SessionLocal()
        try:
            company = session.query(Company).filter_by(id=1).first()
            if not company:
                company = Company(id=1, name="الشركة الافتراضية")
                session.add(company)
                session.commit()

            owner = session.query(Employee).filter_by(role="owner").first()
            if not owner:
                owner = Employee(
                    name="المالك الافتراضي",
                    username="owner",
                    role="owner",
                    company_id=1
                )
                owner.set_password("Ahmed49654965@@")
                session.add(owner)
                session.commit()
        except Exception as e:
            logging.error("Error creating default data: %s", e)
            return load_offline_employees()
        finally:
            session.close()

        session = SessionLocal()
        all_employees = session.query(Employee).all()
        session.close()
        cache_employees(all_employees)
        return all_employees
    except Exception as e:
        logging.error("Error fetching employees from DB: %s", e)
        return load_offline_employees()

def get_update_url():
    """
    Retrieve the update URL from the company's record or return a default URL.
    """
    try:
        session = SessionLocal()
        company = session.query(Company).filter_by(id=1).first()
        if company and hasattr(company, "version_url") and company.version_url:
            update_url = company.version_url
        else:
            update_url = "https://your-update-url.com"
        session.close()
        return update_url
    except Exception as e:
        logging.error("Error fetching update URL: %s", e)
        return "https://your-update-url.com"

def check_for_update():
    """
    Check if a new version is available and prompt the user to update.
    """
    if CURRENT_VERSION != LATEST_VERSION:
        update_url = get_update_url()
        try:
            with open("last_update_url.txt", "r", encoding="utf-8") as f:
                last_url = f.read().strip()
        except FileNotFoundError:
            last_url = ""
        
        if update_url != last_url:
            response = messagebox.askyesno(
                "New Version Available",
                f"A new version ({LATEST_VERSION}) is available. Would you like to update now?"
            )
            if response:
                webbrowser.open(update_url)
                exit()
            with open("last_update_url.txt", "w", encoding="utf-8") as f:
                f.write(update_url)

# --- Splash Screen Class ---
class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.window_width = 300
        self.window_height = 200
        self.center_window()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.font_cairo = ctk.CTkFont(family="Cairo", size=16)

        self.app_name_label = ctk.CTkLabel(self, text=APP_NAME, font=self.font_cairo)
        self.app_name_label.pack(pady=(20, 5))

        self.label = ctk.CTkLabel(self, text="Connecting to database...", font=self.font_cairo)
        self.label.pack(expand=True, padx=20, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate", width=200)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.window_width // 2)
        y = (screen_height // 2) - (self.window_height // 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def start_loading(self):
        self.db_thread = threading.Thread(target=self.load_db)
        self.db_thread.start()
        self.check_db_thread()

    def load_db(self):
        global employees
        employees = initialize_database()

    def check_db_thread(self):
        if self.db_thread.is_alive():
            current_val = self.progress_bar.get()
            next_val = current_val + 0.02
            if next_val > 1:
                next_val = 1
            self.progress_bar.set(next_val)
            self.after(100, self.check_db_thread)
        else:
            self.progress_bar.set(1)
            if not employees:
                messagebox.showerror("Error", "Failed to load database")
            self.destroy()

# --- Login Window Class ---
class LoginWindow(ctk.CTk):
    def __init__(self, employees_list):
        super().__init__()

        self.window_width = 400
        self.window_height = 400
        self.title(APP_NAME)

        try:
            bg_image = PIL.Image.open("background.png")
            self.bg_img = ctk.CTkImage(bg_image, size=(self.window_width, self.window_height))
            bg_label = ctk.CTkLabel(self, image=self.bg_img, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            logging.error("Error loading background image: %s", e)
            bg_label = ctk.CTkLabel(self, text="Welcome", font=self.font_cairo_16)
            bg_label.place(relx=0.5, rely=0.5, anchor="center")

        self.overrideredirect(True)
        self.create_title_bar()
        self.center_window()

        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.bind("<Return>", lambda event: self.do_login())

        self.employees = employees_list
        self.usernames = [emp.username for emp in self.employees]

        lbl_user = ctk.CTkLabel(self, text="اسم المستخدم:", font=self.font_cairo_16)
        lbl_user.pack(pady=5)

        self.user_combobox = ctk.CTkComboBox(self, values=self.usernames, font=self.font_cairo_16, width=250)
        self.user_combobox.pack(pady=5)

        lbl_pass = ctk.CTkLabel(self, text="كلمة المرور:", font=self.font_cairo_16)
        lbl_pass.pack(pady=5)
        self.entry_pass = ctk.CTkEntry(self, show="*", width=250, font=self.font_cairo_16)
        self.entry_pass.pack(pady=5)

        lbl_co = ctk.CTkLabel(self, text="معرّف الشركة (رقم):", font=self.font_cairo_16)
        lbl_co.pack(pady=5)
        self.entry_co = ctk.CTkEntry(self, width=250, font=self.font_cairo_16)
        self.entry_co.pack(pady=5)

        btn_login = ctk.CTkButton(self, text="دخول", command=self.do_login, font=self.font_cairo_16)
        btn_login.pack(pady=20)

    def create_title_bar(self):
        title_bar = ctk.CTkFrame(self, height=30, fg_color="#2e2e2e")
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<ButtonPress-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)

        minimize_btn = ctk.CTkButton(title_bar, text="_", command=self.iconify, width=30, fg_color="gray", corner_radius=5)
        minimize_btn.pack(side="right", padx=(0, 5), pady=2)

        underline_font = ctk.CTkFont(family="Cairo", size=16, underline=True)
        close_label = ctk.CTkLabel(title_bar, text="Close", font=underline_font, fg_color="transparent")
        close_label.pack(side="right", padx=(0, 5))
        close_label.bind("<Button-1>", lambda e: self.destroy())

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_move(self, event):
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.window_width // 2)
        y = (screen_height // 2) - (self.window_height // 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def do_login(self):
        username = self.user_combobox.get().strip()
        password = self.entry_pass.get().strip()
        co_str = self.entry_co.get().strip()

        if not username or not password or not co_str:
            messagebox.showerror("خطأ", "جميع الحقول مطلوبة.")
            return
        if not co_str.isdigit():
            messagebox.showerror("خطأ", "معرّف الشركة يجب أن يكون رقماً.")
            return

        company_id = int(co_str)
        user = None
        for emp in self.employees:
            if emp.username == username:
                user = emp
                break

        if user and user.check_password(password):
            if user.role != "owner" and user.company_id != company_id:
                messagebox.showerror("خطأ", "معرّف الشركة غير مطابق لهذا المستخدم.")
                return

            self.destroy()
            if user.role == "owner":
                from owner_dashboard import OwnerDashboard
                app_gui = OwnerDashboard(user)
                app_gui.mainloop()
            elif user.role == "manager":
                from manager_dashboard import ManagerDashboard
                app_gui = ManagerDashboard(user)
                app_gui.mainloop()
            else:
                from shipment_checker import ShipmentCheckerApp
                app_gui = ShipmentCheckerApp(user)
                app_gui.mainloop()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة.")

# ----------------------------
# --- FastAPI API Endpoints ---
# ----------------------------
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import datetime
import os

app = FastAPI()

# Data model for attendance record
class AttendanceRecord(BaseModel):
    employee_id: int
    check_type: str  # "check-in" or "check-out"
    latitude: float = None
    longitude: float = None

@app.post("/attendance/")
def record_attendance(record: AttendanceRecord):
    if record.check_type not in ["check-in", "check-out"]:
        raise HTTPException(status_code=400, detail="Invalid check_type")
    try:
        session = SessionLocal()
        if not session.is_active:
            raise HTTPException(status_code=503, detail="Database unavailable")
        new_record = Attendance(
            employee_id=record.employee_id,
            check_type=record.check_type,
            timestamp=datetime.datetime.utcnow(),
            latitude=record.latitude,
            longitude=record.longitude
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        return {"id": new_record.id, "employee_id": new_record.employee_id, "check_type": new_record.check_type, "timestamp": new_record.timestamp}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording attendance: {e}")
    finally:
        session.close()

# Data model for creating an operation task
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    created_by: int
    assigned_to: int

@app.post("/tasks/")
def create_task(task: TaskCreate):
    try:
        session = SessionLocal()
        if not session.is_active:
            raise HTTPException(status_code=503, detail="Database unavailable")
        new_task = OperationTask(
            title=task.title,
            description=task.description,
            created_by=task.created_by,
            assigned_to=task.assigned_to,
            status="pending"
        )
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return {"id": new_task.id, "title": new_task.title, "status": new_task.status}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating task: {e}")
    finally:
        session.close()

# Data model for adding a message to an operation task
class TaskMessageCreate(BaseModel):
    task_id: int
    sender_id: int
    message: str

@app.post("/tasks/message/")
def add_task_message(msg: TaskMessageCreate):
    try:
        session = SessionLocal()
        if not session.is_active:
            raise HTTPException(status_code=503, detail="Database unavailable")
        task = session.query(OperationTask).filter_by(id=msg.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="المهمة غير موجودة")
        new_msg = OperationTaskMessage(
            task_id=msg.task_id,
            sender_id=msg.sender_id,
            message=msg.message,
            timestamp=datetime.datetime.utcnow()
        )
        session.add(new_msg)
        session.commit()
        session.refresh(new_msg)
        return {"id": new_msg.id, "task_id": new_msg.task_id, "sender_id": new_msg.sender_id, "message": new_msg.message}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding task message: {e}")
    finally:
        session.close()

# ----------------------------
# --- Main Execution Section ---
# ----------------------------
if __name__ == "__main__":
    # If the "api" argument is passed, run the FastAPI server
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        host = os.getenv("APP_HOST", "192.168.1.110")
        port = int(os.getenv("APP_PORT", "8000"))
        uvicorn.run("login:app", host=host, port=port, reload=True)
    else:
        splash = SplashScreen()
        splash.start_loading()
        splash.mainloop()

        check_for_update()

        app_gui = LoginWindow(employees)
        app_gui.mainloop()