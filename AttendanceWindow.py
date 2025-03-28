import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from models import SessionLocal, Attendance, Employee

class AttendanceWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("سجل الحضور والإنصراف")
        self.geometry("800x600")
        
        # قسم التقويم: يمكنك استخدام مكتبة tkcalendar، هنا نموذج مبسط باستخدام أزرار اليوم
        days_frame = tk.Frame(self)
        days_frame.pack(pady=10)
        
        # على سبيل المثال، عرض أيام الشهر الحالي
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = (first_day.replace(month=first_day.month % 12 + 1, day=1) - datetime.timedelta(days=1))
        num_days = last_day.day
        
        for day in range(1, num_days+1):
            btn = tk.Button(days_frame, text=str(day), width=4,
                            command=lambda d=day: self.load_attendance_for_day(d))
            btn.grid(row=0, column=day-1, padx=2, pady=2)
        
        # جدول عرض الحضور باستخدام Treeview
        self.tree = ttk.Treeview(self, columns=("employee", "check_in", "check_out"), show="headings")
        self.tree.heading("employee", text="اسم الموظف")
        self.tree.heading("check_in", text="تسجيل الدخول")
        self.tree.heading("check_out", text="تسجيل الخروج")
        self.tree.pack(fill="both", expand=True, pady=10)
        
    def load_attendance_for_day(self, day):
        # استرجاع سجلات الحضور للموظفين في اليوم المحدد
        selected_date = datetime.date.today().replace(day=day)
        session = SessionLocal()
        try:
            # تعديل الاستعلام حسب تصميم جدول Attendance، مثال:
            records = session.query(Attendance).filter(
                Attendance.timestamp >= datetime.datetime.combine(selected_date, datetime.time.min),
                Attendance.timestamp <= datetime.datetime.combine(selected_date, datetime.time.max)
            ).all()
            # مسح الجدول
            for item in self.tree.get_children():
                self.tree.delete(item)
            # إضافة السجلات إلى الجدول
            for rec in records:
                # الحصول على اسم الموظف
                employee = session.query(Employee).filter_by(id=rec.employee_id).first()
                check_in = rec.timestamp.strftime("%H:%M:%S") if rec.check_type == "check-in" else ""
                check_out = rec.timestamp.strftime("%H:%M:%S") if rec.check_type == "check-out" else ""
                self.tree.insert("", "end", values=(employee.name if employee else "N/A", check_in, check_out))
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحميل السجلات: {e}")
        finally:
            session.close()
