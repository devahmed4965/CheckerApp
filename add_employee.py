# add_employee.py

import customtkinter as ctk
from tkinter import messagebox
from models import SessionLocal, Employee

class AddEmployeeWindow(ctk.CTkToplevel):
    def __init__(self, parent, manager_user):
        super().__init__(parent)
        self.manager_user = manager_user
        self.title("إضافة موظف")
        self.geometry("400x300")

        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)

        lbl_name = ctk.CTkLabel(self, text="اسم الموظف:", font=self.font_cairo_16)
        lbl_name.pack(pady=5)
        self.entry_name = ctk.CTkEntry(self, width=250, font=self.font_cairo_16)
        self.entry_name.pack(pady=5)

        lbl_username = ctk.CTkLabel(self, text="اسم المستخدم:", font=self.font_cairo_16)
        lbl_username.pack(pady=5)
        self.entry_username = ctk.CTkEntry(self, width=250, font=self.font_cairo_16)
        self.entry_username.pack(pady=5)

        lbl_password = ctk.CTkLabel(self, text="كلمة المرور:", font=self.font_cairo_16)
        lbl_password.pack(pady=5)
        self.entry_password = ctk.CTkEntry(self, show="*", width=250, font=self.font_cairo_16)
        self.entry_password.pack(pady=5)

        add_btn = ctk.CTkButton(self, text="إضافة", command=self.add_employee, font=self.font_cairo_16)
        add_btn.pack(pady=10)

    def add_employee(self):
        name = self.entry_name.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not name or not username or not password:
            messagebox.showerror("خطأ", "جميع الحقول مطلوبة.")
            return

        session = SessionLocal()
        existing = session.query(Employee).filter_by(username=username).first()
        if existing:
            messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل.")
            session.close()
            return

        new_emp = Employee(
            name=name,
            username=username,
            role="employee",
            company_id=self.manager_user.company_id
        )
        new_emp.set_password(password)

        session.add(new_emp)
        session.commit()
        session.close()

        messagebox.showinfo("نجاح", "تم إضافة الموظف بنجاح.")
        self.master.refresh_employee_list()
        self.destroy()
