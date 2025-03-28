import os
import customtkinter as ctk
from tkinter import messagebox
from models import SessionLocal, Employee, Shipment, Company
from add_manager import AddManagerWindow
from login import LoginWindow

class OwnerDashboard(ctk.CTk):
    def __init__(self, logged_in_owner):
        super().__init__()

        self.logged_in_owner = logged_in_owner
        # تحديث العنوان ليشمل بيانات المستخدم
        self.title(f"لوحة المالك - {logged_in_owner.name} ({logged_in_owner.username}) - الشركة: {logged_in_owner.company_id}")
        self.geometry("1000x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.font_cairo_18_bold = ctk.CTkFont(family="Cairo", size=18, weight="bold")
        
        # تحميل رابط الإصدار الحالي من قاعدة البيانات.
        self.load_version_url()

        # الشريط الجانبي
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        # المحتوى الرئيسي
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True)

        # عرض بيانات المستخدم في الجزء العلوي للمحتوى
        header = ctk.CTkFrame(self.main_frame)
        header.pack(fill="x", padx=10, pady=10)
        info_label = ctk.CTkLabel(
            header,
            text=f"مرحباً {logged_in_owner.name} ({logged_in_owner.username}) - معرّف الشركة: {logged_in_owner.company_id}",
            font=self.font_cairo_18_bold
        )
        info_label.pack(padx=10, pady=10)
        
        # أزرار الشريط الجانبي
        add_manager_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="إضافة مدير",
            command=self.open_add_manager,
            font=self.font_cairo_16
        )
        add_manager_btn.pack(pady=20, fill="x")
        report_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="عرض تقارير الشحنات المفحوصة",
            command=self.open_inspection_report,
            font=self.font_cairo_16
        )
        report_btn.pack(pady=20, fill="x")
        clear_shipments_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="حذف كل الشحنات وتحرير المساحة",
            command=self.clear_shipments,
            font=self.font_cairo_16
        )
        clear_shipments_btn.pack(pady=20, fill="x")
        change_url_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="تغيير رابط الإصدار",
            command=self.change_version_url,
            font=self.font_cairo_16
        )
        change_url_btn.pack(pady=20, fill="x")
        logout_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="تسجيل الخروج",
            command=self.logout,
            font=self.font_cairo_16
        )
        logout_btn.pack(pady=20, fill="x")

        # بناء المحتوى الرئيسي
        self.build_main_content()

        # تحديث الإحصائيات العامة
        self.refresh_global_stats()

    def load_version_url(self):
        session = SessionLocal()
        company = session.query(Company).filter_by(id=self.logged_in_owner.company_id).first()
        if company and company.version_url:
            self.version_url = company.version_url
        else:
            self.version_url = "http://current-version-url.com"
        session.close()

    def build_main_content(self):
        # هنا يمكنك إضافة المزيد من المحتوى حسب الحاجة
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="", font=self.font_cairo_16)
        self.stats_label.pack(pady=5)
        self.manager_frame = ctk.CTkFrame(self.main_frame)
        self.manager_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_manager_list()

    def refresh_global_stats(self):
        session = SessionLocal()
        total_managers = session.query(Employee).filter_by(role='manager').count()
        total_employees = session.query(Employee).filter_by(role='employee').count()
        total_companies = session.query(Company).count()
        total_shipments = session.query(Shipment).count()
        checked_shipments = session.query(Shipment).filter_by(checked=True).count()
        session.close()
        stats_text = (
            f"إحصائيات عامة:\n"
            f"عدد المدراء: {total_managers}\n"
            f"عدد الموظفين: {total_employees}\n"
            f"عدد الشركات: {total_companies}\n"
            f"إجمالي الشحنات: {total_shipments}\n"
            f"الشحنات المفحوصة: {checked_shipments}\n"
            f"رابط الإصدار الحالي: {self.version_url}"
        )
        self.stats_label.configure(text=stats_text)

    def refresh_manager_list(self):
        for widget in self.manager_frame.winfo_children():
            widget.destroy()
        session = SessionLocal()
        managers = session.query(Employee).filter_by(role='manager').all()
        session.close()
        for mgr in managers:
            row_frame = ctk.CTkFrame(self.manager_frame)
            row_frame.pack(fill="x", padx=5, pady=5)
            lbl_name = ctk.CTkLabel(row_frame, text=mgr.name, font=self.font_cairo_16)
            lbl_name.pack(side="left", padx=10)
            edit_btn = ctk.CTkButton(
                row_frame,
                text="تعديل",
                command=lambda m=mgr: self.edit_manager(m),
                width=60,
                font=self.font_cairo_16
            )
            edit_btn.pack(side="left", padx=5)
            remove_btn = ctk.CTkButton(
                row_frame,
                text="حذف",
                command=lambda m=mgr: self.remove_manager(m),
                fg_color="red",
                hover_color="#ff4d4d",
                width=60,
                font=self.font_cairo_16
            )
            remove_btn.pack(side="left", padx=5)

    def edit_manager(self, mgr):
        new_name = ctk.CTkInputDialog(
            title="تعديل مدير",
            text=f"الاسم الحالي: {mgr.name}\nأدخل الاسم الجديد:"
        ).get_input()
        if not new_name:
            return
        session = SessionLocal()
        mgr_obj = session.query(Employee).filter_by(id=mgr.id).first()
        if mgr_obj:
            mgr_obj.name = new_name
            session.commit()
        session.close()
        self.refresh_manager_list()
        self.refresh_global_stats()

    def remove_manager(self, mgr):
        if messagebox.askyesno("تأكيد", f"هل تريد حذف المدير {mgr.name}؟"):
            session = SessionLocal()
            mgr_obj = session.query(Employee).filter_by(id=mgr.id).first()
            if mgr_obj:
                session.delete(mgr_obj)
                session.commit()
            session.close()
            self.refresh_manager_list()
            self.refresh_global_stats()

    def open_add_manager(self):
        add_mgr_win = AddManagerWindow(self)
        add_mgr_win.grab_set()
        self.wait_window(add_mgr_win)
        self.refresh_manager_list()
        self.refresh_global_stats()

    def open_inspection_report(self):
        report_win = ctk.CTkToplevel(self)
        report_win.title("تقارير الشحنات المفحوصة")
        report_win.geometry("800x600")
        from tkinter import ttk
        tree = ttk.Treeview(report_win, columns=("ShipmentID", "Date", "Inspector"), show="headings")
        tree.heading("ShipmentID", text="رقم الشحنة")
        tree.heading("Date", text="تاريخ الفحص")
        tree.heading("Inspector", text="من قام بالفحص")
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        session = SessionLocal()
        shipments = session.query(Shipment).filter(Shipment.checked == True).all()
        for s in shipments:
            inspector_name = "غير محدد"
            if s.inspected_by:
                emp = session.query(Employee).filter(Employee.id == s.inspected_by).first()
                if emp:
                    inspector_name = emp.name
            tree.insert("", "end", values=(s.shipment_id, s.inspected_date, inspector_name))
        session.close()

    def clear_shipments(self):
        answer = messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الشحنات من قاعدة البيانات؟")
        if not answer:
            return
        deleted_count = 0
        session = SessionLocal()
        try:
            deleted_count = session.query(Shipment).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل حذف الشحنات: {e}")
            return
        finally:
            session.close()
        messagebox.showinfo("نجاح", f"تم حذف {deleted_count} شحنة.")
        self.refresh_global_stats()

    def change_version_url(self):
        new_url = ctk.CTkInputDialog(
            title="تغيير رابط الإصدار",
            text="أدخل رابط الإصدار الجديد:"
        ).get_input()
        if new_url:
            self.version_url = new_url
            session = SessionLocal()
            company = session.query(Company).filter_by(id=self.logged_in_owner.company_id).first()
            if company:
                company.version_url = new_url
                session.commit()
            session.close()
            messagebox.showinfo("نجاح", "تم تحديث رابط الإصدار بنجاح.")
            self.refresh_global_stats()
        else:
            messagebox.showerror("خطأ", "لم يتم إدخال رابط صالح.")

    def logout(self):
        self.destroy()
        from login import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()

if __name__ == "__main__":
    from login import LoginWindow
    class DummyUser:
        def __init__(self):
            self.name = "المالك"
            self.username = "owner"
            self.role = "owner"
            self.id = 1
            self.company_id = 1
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = OwnerDashboard(DummyUser())
    app.mainloop()
