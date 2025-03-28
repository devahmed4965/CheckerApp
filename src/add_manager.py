# add_manager.py

import customtkinter as ctk
from tkinter import messagebox
from models import SessionLocal, Employee, Company

class AddManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("إضافة مدير")
        self.geometry("400x500")

        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)

        lbl_name = ctk.CTkLabel(self, text="اسم المدير:", font=self.font_cairo_16)
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

        lbl_company_id = ctk.CTkLabel(self, text="معرّف الشركة:", font=self.font_cairo_16)
        lbl_company_id.pack(pady=5)
        self.entry_company_id = ctk.CTkEntry(self, width=250, font=self.font_cairo_16)
        self.entry_company_id.pack(pady=5)

        lbl_company_name = ctk.CTkLabel(self, text="اسم الشركة (إذا كانت جديدة):", font=self.font_cairo_16)
        lbl_company_name.pack(pady=5)
        self.entry_company_name = ctk.CTkEntry(self, width=250, font=self.font_cairo_16)
        self.entry_company_name.pack(pady=5)

        add_btn = ctk.CTkButton(self, text="إضافة", command=self.add_manager, font=self.font_cairo_16)
        add_btn.pack(pady=10)

    def add_manager(self):
        name = self.entry_name.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        co_str = self.entry_company_id.get().strip()
        co_name = self.entry_company_name.get().strip()

        if not name or not username or not password or not co_str:
            messagebox.showerror("خطأ", "جميع الحقول مطلوبة (بما فيها معرف الشركة).")
            return

        if not co_str.isdigit():
            messagebox.showerror("خطأ", "معرّف الشركة يجب أن يكون رقماً.")
            return
        company_id = int(co_str)

        session = SessionLocal()
        company_obj = session.query(Company).filter_by(id=company_id).first()
        if not company_obj:
            if not co_name:
                session.close()
                messagebox.showerror("خطأ", f"لا توجد شركة بمعرّف {company_id} ولم يتم إدخال اسم الشركة.")
                return
            new_co = Company(id=company_id, name=co_name)
            session.add(new_co)
            session.commit()
            company_obj = new_co
            messagebox.showinfo("نجاح", f"تم إنشاء الشركة '{co_name}' بمعرّف {company_id} بنجاح.")

        existing_user = session.query(Employee).filter_by(username=username).first()
        if existing_user:
            session.close()
            messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل.")
            return

        new_mgr = Employee(
            name=name,
            username=username,
            role="manager",
            company_id=company_obj.id
        )
        new_mgr.set_password(password)

        session.add(new_mgr)
        session.commit()
        session.close()

        messagebox.showinfo("نجاح", "تم إضافة المدير بنجاح.")
        if hasattr(self.master, 'refresh_manager_list'):
            self.master.refresh_manager_list()
        self.destroy()
