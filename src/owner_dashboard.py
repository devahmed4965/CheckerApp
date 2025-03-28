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
        self.title("Owner Dashboard")
        self.geometry("1000x700")

        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.font_cairo_18_bold = ctk.CTkFont(family="Cairo", size=18, weight="bold")
        
        # Load the current version URL from the Company record in the database.
        self.load_version_url()

        # Left sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True)

        # Sidebar buttons
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

        # Button: Clear all shipments and free up DB storage
        clear_shipments_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="حذف كل الشحنات وتحرير المساحة",
            command=self.clear_shipments,
            font=self.font_cairo_16
        )
        clear_shipments_btn.pack(pady=20, fill="x")
        
        # New button: Change version URL if available
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

        # Build the main content area (managers list + stats)
        self.build_main_content()

        # Refresh the global stats
        self.refresh_global_stats()

    def load_version_url(self):
        """Load the version URL from the Company record in the database."""
        session = SessionLocal()
        company = session.query(Company).filter_by(id=self.logged_in_owner.company_id).first()
        if company and company.version_url:
            self.version_url = company.version_url
        else:
            # Use a default URL if none is found
            self.version_url = "http://current-version-url.com"
        session.close()

    def build_main_content(self):
        # Stats frame for overall system info
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.pack(fill="x", padx=20, pady=10)

        self.stats_label = ctk.CTkLabel(self.stats_frame, text="", font=self.font_cairo_16)
        self.stats_label.pack(pady=5)

        # In main_frame, place manager list
        self.manager_frame = ctk.CTkFrame(self.main_frame)
        self.manager_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh_manager_list()

    def refresh_global_stats(self):
        """Display overall system info: total managers, employees, shipments, etc."""
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
        self.refresh_global_stats()  # Update stats if needed

    def remove_manager(self, mgr):
        if messagebox.askyesno("تأكيد", f"هل تريد حذف المدير {mgr.name}؟"):
            session = SessionLocal()
            mgr_obj = session.query(Employee).filter_by(id=mgr.id).first()
            if mgr_obj:
                session.delete(mgr_obj)
                session.commit()
            session.close()
            self.refresh_manager_list()
            self.refresh_global_stats()  # Refresh stats after removal

    def open_add_manager(self):
        add_mgr_win = AddManagerWindow(self)
        add_mgr_win.grab_set()
        self.wait_window(add_mgr_win)
        self.refresh_manager_list()
        self.refresh_global_stats()  # Refresh stats after adding

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
        """Delete all shipment records and display the current database file size."""
        answer = messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الشحنات من قاعدة البيانات؟")
        if not answer:
            return

        deleted_count = 0
        session = SessionLocal()
        try:
            # Delete all shipment records
            deleted_count = session.query(Shipment).delete()
            session.commit()

            # If using SQLite, run VACUUM to reclaim disk space
            bind = session.get_bind()
            if bind.dialect.name == 'sqlite':
                session.execute("VACUUM")
                session.commit()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل حذف الشحنات: {e}")
            return
        finally:
            session.close()

        # Assume the database file is named "database.db" in the same directory.
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
        if os.path.exists(db_file):
            size_bytes = os.path.getsize(db_file)
            size_mb = size_bytes / (1024 * 1024)
            messagebox.showinfo("نجاح", f"تم حذف {deleted_count} شحنة.\nحجم ملف قاعدة البيانات: {size_mb:.2f} ميجابايت")
        else:
            messagebox.showinfo("نجاح", f"تم حذف {deleted_count} شحنة.\nلم يتم العثور على ملف قاعدة البيانات لتحديد الحجم.")

        # Refresh global stats after deletion
        self.refresh_global_stats()

    def change_version_url(self):
        """Allows the owner to update the version URL if a new version is available."""
        new_url = ctk.CTkInputDialog(
            title="تغيير رابط الإصدار",
            text="أدخل رابط الإصدار الجديد:"
        ).get_input()
        if new_url:
            self.version_url = new_url
            # Update the version URL in the Company record of the database.
            session = SessionLocal()
            company = session.query(Company).filter_by(id=self.logged_in_owner.company_id).first()
            if company:
                company.version_url = new_url
                session.commit()
            session.close()
            messagebox.showinfo("نجاح", "تم تحديث رابط الإصدار بنجاح.")
            self.refresh_global_stats()  # Update stats to show the new version URL
        else:
            messagebox.showerror("خطأ", "لم يتم إدخال رابط صالح.")

    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

if __name__ == "__main__":
    from login import LoginWindow
    class DummyUser:
        def __init__(self):
            self.name = "المالك"
            self.role = "owner"
            self.id = 1
            self.company_id = 1

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = OwnerDashboard(DummyUser())
    app.mainloop()
