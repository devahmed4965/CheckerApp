import threading
import customtkinter as ctk
from tkinter import messagebox
import logging
import json
import PIL.Image  # Pillow required to work with images
import webbrowser
from models import SessionLocal, Employee, Company, create_tables
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global list to hold employees fetched from the DB or loaded from cache
employees = []
OFFLINE_EMP_CACHE = "offline_employees_cache.json"
APP_NAME = "البوصلة"  # Unique app name

# Version Information
CURRENT_VERSION = "1.0.0"
# In a real application, you might fetch this from a server or configuration
LATEST_VERSION = "1.1.0"

def cache_employees(employees_list):
    """
    Save employee data locally so that if the online DB is unreachable later,
    we can still allow users to log in.
    """
    data = []
    for emp in employees_list:
        data.append({
            "name": emp.name,
            "username": emp.username,
            "role": emp.role,
            "company_id": emp.company_id,
            # For demo purposes, we store the default password.
            # In production, store only password hashes.
            "password": "Ahmed49654965@@"
        })
    try:
        with open(OFFLINE_EMP_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logging.error("Error caching employees: %s", e)

def load_offline_employees():
    """
    Load employees from a local JSON file.
    This is used when the online database is unreachable.
    """
    employees_list = []
    try:
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
        # Fallback: return a default offline employee
        default_emp = Employee(name="Offline Owner", username="owner", role="owner", company_id=1)
        default_emp.set_password("Ahmed49654965@@")
        return [default_emp]

def initialize_database():
    """
    Create tables, add default data, and fetch all employees.
    Returns the list of Employee objects.
    """
    create_tables()

    # Create default data if needed
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
            owner.set_password("Ahmed49654965@@")  # default password
            session.add(owner)
            session.commit()
    except Exception as e:
        logging.error("Error creating default data: %s", e)
    finally:
        session.close()

    # Now fetch employees for use in the LoginWindow
    try:
        session = SessionLocal()
        all_employees = session.query(Employee).all()
        session.close()
        # Cache employees for offline use
        cache_employees(all_employees)
        return all_employees
    except Exception as e:
        logging.error("Error fetching employees from DB: %s", e)
        # Fallback: load employees from offline cache
        return load_offline_employees()

def get_update_url():
    """
    Retrieve the update URL from the Company record.
    If unavailable, return a default URL.
    """
    try:
        session = SessionLocal()
        company = session.query(Company).filter_by(id=1).first()  # Using default company id = 1
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
    Check if a new version is available.
    The pop-up window appears only if a new update URL is set (i.e. it differs from the last notified URL).
    """
    if CURRENT_VERSION != LATEST_VERSION:
        update_url = get_update_url()
        # Try to load the last notified update URL from a file
        try:
            with open("last_update_url.txt", "r", encoding="utf-8") as f:
                last_url = f.read().strip()
        except FileNotFoundError:
            last_url = ""
        
        # Only prompt if the URL has changed since the last notification.
        if update_url != last_url:
            response = messagebox.askyesno(
                "New Version Available",
                f"A new version ({LATEST_VERSION}) is available. Would you like to update now?"
            )
            if response:
                webbrowser.open(update_url)
                exit()
            # Save the current update URL to file so that the pop-up doesn't show again next time.
            with open("last_update_url.txt", "w", encoding="utf-8") as f:
                f.write(update_url)

# --- Splash Screen Class ---
class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)  # Remove OS window decorations
        self.window_width = 300
        self.window_height = 200
        self.center_window()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.font_cairo = ctk.CTkFont(family="Cairo", size=16)

        # Display the unique app name on the splash screen
        self.app_name_label = ctk.CTkLabel(
            self,
            text=APP_NAME,
            font=self.font_cairo
        )
        self.app_name_label.pack(pady=(20, 5))

        # Label for the loading message
        self.label = ctk.CTkLabel(
            self,
            text="Connecting to database...",
            font=self.font_cairo
        )
        self.label.pack(expand=True, padx=20, pady=5)

        # A progress bar to simulate loading
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate", width=200)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)  # start at 0%

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.window_width // 2)
        y = (screen_height // 2) - (self.window_height // 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def start_loading(self):
        """
        Start the background thread for DB initialization and begin checking for completion.
        """
        self.db_thread = threading.Thread(target=self.load_db)
        self.db_thread.start()
        self.check_db_thread()

    def load_db(self):
        """
        Runs in a background thread to initialize the DB.
        """
        global employees
        employees = initialize_database()

    def check_db_thread(self):
        """
        Periodically check if the DB thread is done.
        Meanwhile, update the progress bar for a simple loading effect.
        """
        if self.db_thread.is_alive():
            current_val = self.progress_bar.get()
            next_val = current_val + 0.02
            if next_val > 1:
                next_val = 1
            self.progress_bar.set(next_val)
            self.after(100, self.check_db_thread)
        else:
            self.progress_bar.set(1)
            self.destroy()  # Close the splash screen

# --- Login Window Class with Custom Title Bar and Background Image ---
class LoginWindow(ctk.CTk):
    def __init__(self, employees_list):
        super().__init__()

        # Set window dimensions and title
        self.window_width = 400
        self.window_height = 400
        self.title(APP_NAME)

        # Load and set the background image (update the file path as needed)
        try:
            bg_image = PIL.Image.open("background.png")
            self.bg_img = ctk.CTkImage(bg_image, size=(self.window_width, self.window_height))
            bg_label = ctk.CTkLabel(self, image=self.bg_img, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            logging.error("Error loading background image: %s", e)

        # Remove OS window decorations and create custom title bar
        self.overrideredirect(True)
        self.create_title_bar()
        self.center_window()

        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.bind("<Return>", lambda event: self.do_login())

        # Use the employee list loaded during DB initialization (or from cache)
        self.employees = employees_list
        self.usernames = [emp.username for emp in self.employees]

        # Create login widgets on top of the background image
        lbl_user = ctk.CTkLabel(self, text="اسم المستخدم:", font=self.font_cairo_16)
        lbl_user.pack(pady=5)

        self.user_combobox = ctk.CTkComboBox(
            self,
            values=self.usernames,
            font=self.font_cairo_16,
            width=250
        )
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
        """Creates a custom title bar with minimize and underlined close controls."""
        title_bar = ctk.CTkFrame(self, height=30, fg_color="#2e2e2e")
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<ButtonPress-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)

        minimize_btn = ctk.CTkButton(
            title_bar,
            text="_",
            command=self.iconify,
            width=30,
            fg_color="gray",
            corner_radius=5
        )
        minimize_btn.pack(side="right", padx=(0, 5), pady=2)

        underline_font = ctk.CTkFont(family="Cairo", size=16, underline=True)
        close_label = ctk.CTkLabel(
            title_bar,
            text="Close",
            font=underline_font,
            fg_color="transparent"
        )
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
        # Search in the cached employee list (loaded during splash)
        for emp in self.employees:
            if emp.username == username:
                user = emp
                break

        if user and user.check_password(password):
            if user.role != "owner" and user.company_id != company_id:
                messagebox.showerror("خطأ", "معرّف الشركة غير مطابق لهذا المستخدم.")
                return

            self.destroy()
            # Launch the appropriate dashboard based on user role
            if user.role == "owner":
                from owner_dashboard import OwnerDashboard
                app = OwnerDashboard(user)
                app.mainloop()
            elif user.role == "manager":
                from manager_dashboard import ManagerDashboard
                app = ManagerDashboard(user)
                app.mainloop()
            else:
                from shipment_checker import ShipmentCheckerApp
                app = ShipmentCheckerApp(user)
                app.mainloop()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة.")

# --- Main Execution ---
if __name__ == "__main__":
    # 1) Show the splash screen with a progress bar and initialize the DB/Employees
    splash = SplashScreen()
    splash.start_loading()  # Starts the background DB thread
    splash.mainloop()

    # 2) Check if a new version is available before launching the login window.
    check_for_update()

    # 3) After update check (or if user chooses not to update), open the login window.
    app = LoginWindow(employees)
    app.mainloop()
