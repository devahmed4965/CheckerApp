import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import datetime
import calendar
import pandas as pd
from models import SessionLocal, Attendance, Employee

# Set CustomTkinter appearance and theme
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # You can change this as needed

# Delay font creation until after a root window is available:
def get_cairo_font(size=14, weight="normal"):
    return ctk.CTkFont(family="Cairo", size=size, weight=weight)

class AttendanceWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        # Now that the root exists, we can create fonts:
        self.cairo_font_header = get_cairo_font(18, "bold")
        self.default_font = get_cairo_font(14)
        
        self.title("سجل الحضور والانصراف")
        self.geometry("1200x800")
        self.state("zoomed")  # Maximize window
        self.resizable(True, True)
        
        # Create a full-screen TabView (Notebook)
        self.notebook = ctk.CTkTabview(self, width=self.winfo_screenwidth()-40, height=self.winfo_screenheight()-100)
        self.notebook.pack(padx=20, pady=20, fill="both", expand=True)
        self.notebook.add("Daily")
        self.notebook.add("Monthly")
        
        self.build_daily_tab()
        self.build_monthly_tab()
    
    def build_daily_tab(self):
        daily_tab = self.notebook.tab("Daily")
        daily_tab.configure(fg_color="#ffffff")
        
        # Header frame with icon and title
        header_frame = ctk.CTkFrame(daily_tab, corner_radius=10, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=20, pady=10)
        try:
            attendance_icon = ctk.CTkImage(
                light_image=tk.PhotoImage(file="attendance_icon.png"),
                dark_image=tk.PhotoImage(file="attendance_icon.png"),
                size=(30, 30)
            )
        except Exception as e:
            print(f"Error loading attendance icon: {e}")
            attendance_icon = None
        
        header_label = ctk.CTkLabel(header_frame, text="سجل الحضور اليومي",
                                     font=self.cairo_font_header,
                                     image=attendance_icon, compound="left")
        header_label.pack(padx=10, pady=10)
        
        # Frame for day buttons
        days_frame = ctk.CTkFrame(daily_tab, corner_radius=10)
        days_frame.pack(padx=20, pady=10, fill="x")
        
        today = datetime.date.today()
        first_day = today.replace(day=1)
        try:
            # Calculate the first day of next month:
            next_month = today.month % 12 + 1
            if today.month == 12:
                next_month_first_day = today.replace(year=today.year+1, month=1, day=1)
            else:
                next_month_first_day = today.replace(month=next_month, day=1)
        except ValueError:
            next_month_first_day = today.replace(year=today.year+1, month=1, day=1)
        last_day = next_month_first_day - datetime.timedelta(days=1)
        num_days = last_day.day
        
        for day in range(1, num_days+1):
            btn = ctk.CTkButton(days_frame, text=str(day), width=40,
                                font=self.default_font,
                                command=lambda d=day: self.load_daily_attendance(d))
            btn.grid(row=0, column=day-1, padx=3, pady=3)
        
        # Frame for the Treeview with a scrollbar
        tree_frame = ctk.CTkFrame(daily_tab, corner_radius=10)
        tree_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.daily_tree = ttk.Treeview(tree_frame, columns=("employee", "check_in", "check_out"),
                                       show="headings", height=10)
        self.daily_tree.heading("employee", text="اسم الموظف")
        self.daily_tree.heading("check_in", text="تسجيل الدخول")
        self.daily_tree.heading("check_out", text="تسجيل الخروج")
        self.daily_tree.column("employee", width=200, anchor="center")
        self.daily_tree.column("check_in", width=150, anchor="center")
        self.daily_tree.column("check_out", width=150, anchor="center")
        self.daily_tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.daily_tree.yview)
        self.daily_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def load_daily_attendance(self, day):
        try:
            selected_date = datetime.date.today().replace(day=day)
        except ValueError as ve:
            messagebox.showerror("خطأ", f"Invalid day: {ve}")
            return

        print(f"Loading attendance for date: {selected_date}")
        # Define boundaries (adjust if your data is stored in UTC)
        start_dt = datetime.datetime.combine(selected_date, datetime.time.min)
        end_dt = datetime.datetime.combine(selected_date, datetime.time.max)
        print(f"Query range: {start_dt} to {end_dt}")
        
        session = SessionLocal()
        try:
            records = session.query(Attendance).filter(
                Attendance.timestamp >= start_dt,
                Attendance.timestamp <= end_dt
            ).all()
            print(f"Found {len(records)} records for {selected_date}")
            # Clear the treeview
            for item in self.daily_tree.get_children():
                self.daily_tree.delete(item)
            for rec in records:
                employee = session.query(Employee).filter_by(id=rec.employee_id).first()
                check_in = rec.timestamp.strftime("%H:%M:%S") if rec.check_type == "check-in" else ""
                check_out = rec.timestamp.strftime("%H:%M:%S") if rec.check_type == "check-out" else ""
                self.daily_tree.insert("", "end", values=(employee.name if employee else "N/A", check_in, check_out))
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحميل السجلات: {e}")
        finally:
            session.close()
    
    def build_monthly_tab(self):
        monthly_tab = self.notebook.tab("Monthly")
        monthly_tab.configure(fg_color="#ffffff")
        
        # Header frame for Monthly tab
        header_frame = ctk.CTkFrame(monthly_tab, corner_radius=10, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=20, pady=10)
        try:
            report_icon = ctk.CTkImage(
                light_image=tk.PhotoImage(file="report_icon.png"),
                dark_image=tk.PhotoImage(file="report_icon.png"),
                size=(30, 30)
            )
        except Exception as e:
            print(f"Error loading report icon: {e}")
            report_icon = None
        header_label = ctk.CTkLabel(header_frame, text="السجل الشهري",
                                    font=self.cairo_font_header,
                                    image=report_icon, compound="left")
        header_label.pack(padx=10, pady=10)
        
        # Control frame for month and year selection
        control_frame = ctk.CTkFrame(monthly_tab, corner_radius=10)
        control_frame.pack(padx=20, pady=10, fill="x")
        
        lbl_month = ctk.CTkLabel(control_frame, text="الشهر:", font=get_cairo_font(14))
        lbl_month.grid(row=0, column=0, padx=5, pady=5)
        
        self.month_var = tk.StringVar(value=str(datetime.date.today().month))
        month_options = [str(i) for i in range(1, 13)]
        self.month_cb = ttk.Combobox(control_frame, textvariable=self.month_var, values=month_options, width=5, state="readonly")
        self.month_cb.grid(row=0, column=1, padx=5, pady=5)
        
        lbl_year = ctk.CTkLabel(control_frame, text="السنة:", font=get_cairo_font(14))
        lbl_year.grid(row=0, column=2, padx=5, pady=5)
        
        self.year_var = tk.StringVar(value=str(datetime.date.today().year))
        year_options = [str(y) for y in range(datetime.date.today().year - 5, datetime.date.today().year + 6)]
        self.year_cb = ttk.Combobox(control_frame, textvariable=self.year_var, values=year_options, width=7, state="readonly")
        self.year_cb.grid(row=0, column=3, padx=5, pady=5)
        
        load_btn = ctk.CTkButton(control_frame, text="تحميل السجل الشهري", font=get_cairo_font(14),
                                 command=self.load_monthly_attendance)
        load_btn.grid(row=0, column=4, padx=10, pady=5)
        
        export_btn = ctk.CTkButton(control_frame, text="تصدير السجل الشهري", font=get_cairo_font(14),
                                   command=self.export_monthly_attendance)
        export_btn.grid(row=0, column=5, padx=10, pady=5)
        
        # Treeview for monthly summary
        tree_frame = ctk.CTkFrame(monthly_tab, corner_radius=10)
        tree_frame.pack(padx=20, pady=10, fill="both", expand=True)
        self.monthly_tree = ttk.Treeview(tree_frame,
                                         columns=("employee", "present_days", "absent_days", "total_hours"),
                                         show="headings", height=10)
        self.monthly_tree.heading("employee", text="اسم الموظف")
        self.monthly_tree.heading("present_days", text="أيام الحضور")
        self.monthly_tree.heading("absent_days", text="أيام الغياب")
        self.monthly_tree.heading("total_hours", text="إجمالي وقت العمل (ساعات)")
        self.monthly_tree.column("employee", width=200, anchor="center")
        self.monthly_tree.column("present_days", width=100, anchor="center")
        self.monthly_tree.column("absent_days", width=100, anchor="center")
        self.monthly_tree.column("total_hours", width=150, anchor="center")
        self.monthly_tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.monthly_tree.yview)
        self.monthly_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def load_monthly_attendance(self):
        try:
            month = int(self.month_var.get())
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("خطأ", "الرجاء اختيار شهر وسنة صالحين")
            return
        
        num_days = calendar.monthrange(year, month)[1]
        session = SessionLocal()
        try:
            employees_list = session.query(Employee).all()
            summary_data = []
            for emp in employees_list:
                start_date = datetime.date(year, month, 1)
                end_date = datetime.date(year, month, num_days)
                records = session.query(Attendance).filter(
                    Attendance.employee_id == emp.id,
                    Attendance.timestamp >= datetime.datetime.combine(start_date, datetime.time.min),
                    Attendance.timestamp <= datetime.datetime.combine(end_date, datetime.time.max)
                ).all()
                daily_records = {}
                for rec in records:
                    rec_date = rec.timestamp.date()
                    if rec_date not in daily_records:
                        daily_records[rec_date] = {"check_in": None, "check_out": None}
                    if rec.check_type == "check-in" and daily_records[rec_date]["check_in"] is None:
                        daily_records[rec_date]["check_in"] = rec.timestamp
                    elif rec.check_type == "check-out":
                        daily_records[rec_date]["check_out"] = rec.timestamp
                present_days = 0
                total_seconds = 0
                for day in range(1, num_days+1):
                    cur_date = datetime.date(year, month, day)
                    if cur_date in daily_records:
                        recs = daily_records[cur_date]
                        if recs["check_in"] and recs["check_out"]:
                            present_days += 1
                            diff = recs["check_out"] - recs["check_in"]
                            total_seconds += diff.total_seconds()
                absent_days = num_days - present_days
                total_hours = round(total_seconds / 3600, 2)
                summary_data.append({
                    "employee": emp.name,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "total_hours": total_hours
                })
            for item in self.monthly_tree.get_children():
                self.monthly_tree.delete(item)
            for row in summary_data:
                self.monthly_tree.insert("", "end", values=(row["employee"], row["present_days"],
                                                             row["absent_days"], row["total_hours"]))
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحميل السجل الشهري: {e}")
        finally:
            session.close()
    
    def export_monthly_attendance(self):
        data = []
        for child in self.monthly_tree.get_children():
            vals = self.monthly_tree.item(child, "values")
            data.append({
                "اسم الموظف": vals[0],
                "أيام الحضور": vals[1],
                "أيام الغياب": vals[2],
                "إجمالي وقت العمل (ساعات)": vals[3]
            })
        if not data:
            messagebox.showwarning("تنبيه", "لا توجد بيانات للتصدير!")
            return
        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="اختر مكان حفظ ملف Excel"
        )
        if not file_path:
            return
        try:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("نجاح", "تم تصدير السجل الشهري بنجاح!")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تصدير الملف: {e}")
    
    # ----------------------------------------------------------------
    # The remaining functions below (employee management, shipment, etc.)
    # are not directly related to the attendance functionality.
    # ----------------------------------------------------------------
    
    def logout(self):
        self.destroy()
        from login import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()
    
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    app_window = AttendanceWindow(root)
    app_window.mainloop()
