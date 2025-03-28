import os
import sys
import logging
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import datetime
import pandas as pd  # For CSV handling
from models import SessionLocal, Employee, Shipment, Company
from add_manager import AddManagerWindow
from login import LoginWindow

# Optional: load icons if available (requires Pillow)
try:
    from PIL import Image
except ImportError:
    Image = None

# Use sys._MEIPASS when frozen (EXE mode)
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    filename=os.path.join(base_dir, 'manager_dashboard.log'),
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ----------------------------------------------------------------------------------------
# Manager Dashboard
# ----------------------------------------------------------------------------------------
class ManagerDashboard(ctk.CTk):
    def __init__(self, logged_in_user):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.title(f"لوحة المدير - {logged_in_user.name}")
        self.geometry("1200x800")  # Wider to accommodate sidebar
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Define Cairo fonts
        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.font_cairo_24_bold = ctk.CTkFont(family="Cairo", size=24, weight="bold")

        # Load icons from the proper folder
        self.icon_logout = None
        self.icon_add_emp = None
        self.icon_report = None
        self.icon_activity = None
        self.icon_search = None
        self.load_icons()

        # Layout: Sidebar and main content
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.build_sidebar()
        self.build_main_content()

        # Refresh dashboard stats
        self.refresh_company_stats()
        self.refresh_employee_list()

    def load_icons(self):
        """Load icons from 'icons' folder located in base_dir."""
        icons_path = os.path.join(base_dir, "icons")
        if Image is None:
            return
        try:
            self.icon_logout = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_path, "logout.png")),
                dark_image=Image.open(os.path.join(icons_path, "logout.png")),
                size=(20, 20)
            )
            self.icon_add_emp = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_path, "add_employee.png")),
                dark_image=Image.open(os.path.join(icons_path, "add_employee.png")),
                size=(20, 20)
            )
            self.icon_report = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_path, "report.png")),
                dark_image=Image.open(os.path.join(icons_path, "report.png")),
                size=(20, 20)
            )
            self.icon_activity = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_path, "activity.png")),
                dark_image=Image.open(os.path.join(icons_path, "activity.png")),
                size=(20, 20)
            )
            self.icon_search = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_path, "search.png")),
                dark_image=Image.open(os.path.join(icons_path, "search.png")),
                size=(20, 20)
            )
        except Exception as e:
            logging.warning(f"Failed to load icons: {e}")

    def build_sidebar(self):
        """Build sidebar buttons including Excel Settings."""
        sidebar_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"مرحباً، {self.logged_in_user.name}",
            font=self.font_cairo_24_bold
        )
        sidebar_label.pack(pady=20)
        btn_add_emp = ctk.CTkButton(
            self.sidebar_frame,
            text="إضافة موظف",
            command=self.add_employee,
            font=self.font_cairo_16,
            cursor="hand2",
            image=self.icon_add_emp,
            compound="left" if self.icon_add_emp else None
        )
        btn_add_emp.pack(pady=10, fill="x")
        btn_report = ctk.CTkButton(
            self.sidebar_frame,
            text="التقرير الشهري",
            command=self.open_monthly_report,
            font=self.font_cairo_16,
            cursor="hand2",
            image=self.icon_report,
            compound="left" if self.icon_report else None
        )
        btn_report.pack(pady=10, fill="x")
        btn_activity = ctk.CTkButton(
            self.sidebar_frame,
            text="نشاط الموظفين",
            command=self.open_employee_inspection_report,
            font=self.font_cairo_16,
            cursor="hand2",
            image=self.icon_activity,
            compound="left" if self.icon_activity else None
        )
        btn_activity.pack(pady=10, fill="x")
        btn_search = ctk.CTkButton(
            self.sidebar_frame,
            text="بحث عن شحنة",
            command=self.search_shipment,
            font=self.font_cairo_16,
            cursor="hand2",
            image=self.icon_search,
            compound="left" if self.icon_search else None
        )
        btn_search.pack(pady=10, fill="x")
        btn_excel_settings = ctk.CTkButton(
            self.sidebar_frame,
            text="إعدادات Excel",
            command=self.open_excel_settings,
            font=self.font_cairo_16,
            cursor="hand2"
        )
        btn_excel_settings.pack(pady=10, fill="x")
        btn_export_pickup = ctk.CTkButton(
            self.sidebar_frame,
            text="تصدير بيانات البيك أب",
            command=self.export_pickup_data,
            font=self.font_cairo_16,
            cursor="hand2"
        )
        btn_export_pickup.pack(pady=10, fill="x")
        btn_import_pickup = ctk.CTkButton(
            self.sidebar_frame,
            text="استيراد بيانات البيك أب",
            command=self.import_pickup_data,
            font=self.font_cairo_16,
            cursor="hand2"
        )
        btn_import_pickup.pack(pady=10, fill="x")
        btn_clear_shipments = ctk.CTkButton(
            self.sidebar_frame,
            text="حذف جميع بيانات الشحنات",
            command=self.delete_all_shipments,
            font=self.font_cairo_16,
            cursor="hand2",
            fg_color="red"
        )
        btn_clear_shipments.pack(pady=10, fill="x")
        btn_logout = ctk.CTkButton(
            self.sidebar_frame,
            text="تسجيل الخروج",
            command=self.logout,
            font=self.font_cairo_16,
            cursor="hand2",
            fg_color="red",
            image=self.icon_logout,
            compound="left" if self.icon_logout else None
        )
        btn_logout.pack(pady=40, fill="x")

    def build_main_content(self):
        """Build the main content area with a scrollable frame."""
        self.content_scroll_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="", corner_radius=0)
        self.content_scroll_frame.pack(fill="both", expand=True)
        top_area = ctk.CTkFrame(self.content_scroll_frame)
        top_area.pack(fill="x", pady=10)
        title = ctk.CTkLabel(top_area, text="لوحة المدير", font=self.font_cairo_24_bold)
        title.pack(side="left", padx=10)
        self.tree_frame = ctk.CTkFrame(self.content_scroll_frame)
        self.tree_frame.pack(fill="both", expand=True, pady=10, padx=10)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("Name", "Username", "Password"),
            show="headings",
            height=10
        )
        self.tree.heading("Name", text="اسم الموظف")
        self.tree.heading("Username", text="اسم المستخدم")
        self.tree.heading("Password", text="كلمة المرور")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")
        btn_frame = ctk.CTkFrame(self.content_scroll_frame)
        btn_frame.pack(pady=10)
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="تعديل موظف",
            command=self.edit_employee,
            font=self.font_cairo_16,
            cursor="hand2"
        )
        edit_btn.grid(row=0, column=0, padx=10)
        remove_btn = ctk.CTkButton(
            btn_frame,
            text="حذف موظف",
            command=self.remove_employee,
            font=self.font_cairo_16,
            fg_color="red",
            cursor="hand2"
        )
        remove_btn.grid(row=0, column=1, padx=10)
        self.stats_frame = ctk.CTkFrame(self.content_scroll_frame, fg_color="#5d5e5e", corner_radius=8)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        stats_header = ctk.CTkLabel(self.stats_frame, text="إحصائيات الشحنات حسب الموظف", font=self.font_cairo_24_bold)
        stats_header.pack(pady=5)
        self.company_stats_frame = ctk.CTkFrame(self.content_scroll_frame)
        self.company_stats_frame.pack(fill="x", padx=10, pady=10)
        self.company_stats_label = ctk.CTkLabel(self.company_stats_frame, text="", font=self.font_cairo_16)
        self.company_stats_label.pack(pady=5)

    def refresh_employee_list(self):
        session = SessionLocal()
        employees = session.query(Employee).filter(
            Employee.company_id == self.logged_in_user.company_id,
            Employee.role == "employee"
        ).all()
        session.close()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp in employees:
            self.tree.insert("", "end", iid=emp.id, values=(emp.name, emp.username, emp.password_plain or ""))
    
    def refresh_shipment_stats(self):
        if hasattr(self, 'stats_frame'):
            self.stats_frame.destroy()
        self.stats_frame = ctk.CTkFrame(self.content_scroll_frame, fg_color="#646664", corner_radius=8)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        stats_header = ctk.CTkLabel(self.stats_frame, text="إحصائيات الشحنات حسب الموظف", font=self.font_cairo_24_bold)
        stats_header.pack(pady=5)
        session = SessionLocal()
        employees = session.query(Employee).filter(
            Employee.company_id == self.logged_in_user.company_id,
            Employee.role == "employee"
        ).all()
        for emp in employees:
            inspected_count = session.query(Shipment).filter(
                Shipment.employee_id == emp.id,
                Shipment.checked == True
            ).count()
            imported_count = session.query(Shipment).filter(
                Shipment.employee_id == emp.id,
                Shipment.imported == True
            ).count()
            stats_line = f"{emp.name}: مفحوصة = {inspected_count}, مستوردة = {imported_count}"
            lbl = ctk.CTkLabel(self.stats_frame, text=stats_line, font=self.font_cairo_16)
            lbl.pack(anchor="w", padx=10, pady=2)
        session.close()

    def refresh_company_stats(self):
        session = SessionLocal()
        total_employees = session.query(Employee).filter(
            Employee.company_id == self.logged_in_user.company_id
        ).count()
        total_shipments = session.query(Shipment).join(Employee, Shipment.employee_id == Employee.id).filter(
            Employee.company_id == self.logged_in_user.company_id
        ).count()
        checked_shipments = session.query(Shipment).join(Employee, Shipment.employee_id == Employee.id).filter(
            Employee.company_id == self.logged_in_user.company_id,
            Shipment.checked == True
        ).count()
        session.close()
        not_checked = total_shipments - checked_shipments
        stats_text = (
            f"إحصائيات الشركة:\n"
            f"عدد الموظفين: {total_employees}\n"
            f"إجمالي الشحنات: {total_shipments}\n"
            f"الشحنات المفحوصة: {checked_shipments}\n"
            f"الشحنات غير المفحوصة: {not_checked}"
        )
        self.company_stats_label.configure(text=stats_text)

    def add_employee(self):
        from add_employee import AddEmployeeWindow
        add_window = AddEmployeeWindow(self, self.logged_in_user)
        add_window.grab_set()
        self.wait_window(add_window)
        self.refresh_employee_list()
        self.refresh_shipment_stats()
        self.refresh_company_stats()

    def edit_employee(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("خطأ", "يرجى اختيار موظف للتعديل.")
            return
        emp_id = int(selected)
        session = SessionLocal()
        emp = session.query(Employee).filter(Employee.id == emp_id).first()
        session.close()
        if not emp:
            messagebox.showerror("خطأ", "الموظف غير موجود.")
            return
        new_name = ctk.CTkInputDialog(
            title="تعديل موظف",
            text=f"الاسم الحالي: {emp.name}\nأدخل الاسم الجديد (اتركه فارغاً إذا لم ترغب في تغييره):",
            font=self.font_cairo_16
        ).get_input()
        new_password = ctk.CTkInputDialog(
            title="تعديل كلمة المرور",
            text=f"كلمة المرور الحالية: {emp.password_plain or 'غير محددة'}\nأدخل كلمة المرور الجديدة (اتركها فارغة إذا لم ترغب في تغييرها):",
            font=self.font_cairo_16
        ).get_input()
        if not new_name and not new_password:
            return
        session = SessionLocal()
        emp_obj = session.query(Employee).filter(Employee.id == emp_id).first()
        if emp_obj:
            if new_name:
                emp_obj.name = new_name
            if new_password:
                emp_obj.password_plain = new_password
            session.commit()
        session.close()
        self.refresh_employee_list()
        self.refresh_shipment_stats()
        self.refresh_company_stats()

    def remove_employee(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("خطأ", "يرجى اختيار موظف للحذف.")
            return
        emp_id = int(selected)
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الموظف؟"):
            return
        session = SessionLocal()
        emp = session.query(Employee).filter(Employee.id == emp_id).first()
        if emp:
            session.delete(emp)
            session.commit()
            messagebox.showinfo("نجاح", "تم حذف الموظف.")
        else:
            messagebox.showerror("خطأ", "الموظف غير موجود.")
        session.close()
        self.refresh_employee_list()
        self.refresh_shipment_stats()
        self.refresh_company_stats()

    def open_add_manager(self):
        add_mgr_win = AddManagerWindow(self)
        add_mgr_win.grab_set()
        self.wait_window(add_mgr_win)
        self.refresh_employee_list()
        self.refresh_shipment_stats()
        self.refresh_company_stats()

    def search_shipment(self):
        shipment_id = ctk.CTkInputDialog(title="بحث عن شحنة", text="أدخل رقم الشحنة:", font=self.font_cairo_16).get_input()
        if not shipment_id:
            return
        shipment_id = shipment_id.strip().lower()
        session = SessionLocal()
        shipment = session.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        session.close()
        if shipment:
            inspector_name = "غير محدد"
            if shipment.inspected_by:
                session = SessionLocal()
                inspector = session.query(Employee).filter(Employee.id == shipment.inspected_by).first()
                session.close()
                if inspector:
                    inspector_name = inspector.name
            details = f"تم الفحص: {'نعم' if shipment.checked else 'لا'}\n"
            details += f"تاريخ الفحص: {shipment.inspected_date}\n"
            details += f"تم الاستلام بواسطة: {inspector_name}"
            messagebox.showinfo("تفاصيل الشحنة", details)
        else:
            messagebox.showerror("الشحنة غير موجودة", "لم يتم العثور على الشحنة.")

    def open_monthly_report(self):
        try:
            from monthly_report import MonthlyReportWindow
            report_win = MonthlyReportWindow(self)
            report_win.grab_set()
        except Exception as e:
            messagebox.showerror("خطأ", f"لا يمكن فتح التقرير الشهري: {e}")

    def open_employee_inspection_report(self):
        # Create a loading window with a progress bar
        loading_win = ctk.CTkToplevel(self)
        loading_win.title("تحميل تقرير نشاط الموظفين")
        loading_win.geometry("300x150")
        loading_win.resizable(False, False)
        loading_label = ctk.CTkLabel(loading_win, text="جارِ تحميل البيانات...", font=self.font_cairo_16)
        loading_label.pack(pady=10, padx=20)
        progress_bar = ctk.CTkProgressBar(loading_win, width=250)
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        progress_value = 0
        def update_progress():
            nonlocal progress_value
            if progress_value < 100:
                progress_value += 1
                progress_bar.set(progress_value / 100)
                loading_label.configure(text=f"جارِ تحميل البيانات... {progress_value}%")
                loading_win.after(20, update_progress)
            else:
                build_report()
        def build_report():
            report_win = ctk.CTkToplevel(self)
            report_win.title("تقرير نشاط الموظفين")
            report_win.geometry("800x600")
            scroll_frame = ctk.CTkScrollableFrame(report_win, corner_radius=0, label_text="")
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
            tree = ttk.Treeview(scroll_frame, columns=("ShipmentID", "Date", "Inspector"), show="headings")
            tree.heading("ShipmentID", text="رقم الشحنة")
            tree.heading("Date", text="تاريخ الفحص")
            tree.heading("Inspector", text="من قام بالفحص")
            tree.pack(fill="both", expand=True)
            session = SessionLocal()
            shipments = session.query(Shipment).join(Employee, Shipment.employee_id == Employee.id).filter(
                Employee.company_id == self.logged_in_user.company_id,
                Shipment.checked == True
            ).all()
            for s in shipments:
                inspector_name = "غير محدد"
                if s.inspected_by:
                    inspector = session.query(Employee).filter(Employee.id == s.inspected_by).first()
                    if inspector:
                        inspector_name = inspector.name
                tree.insert("", "end", values=(s.shipment_id, s.inspected_date, inspector_name))
            session.close()
            loading_win.destroy()
        update_progress()

    # ----------------------------
    # New Functionality: Pickup Data Export/Import and Delete All Shipments
    # ----------------------------
    def export_pickup_data(self):
        session = SessionLocal()
        pickup_shipments = session.query(Shipment).filter(
            Shipment.status.in_(["Pickup", "Line", "Return"])
        ).all()
        session.close()
        if not pickup_shipments:
            messagebox.showinfo("تنبيه", "لا توجد بيانات بيك أب للتصدير.")
            return
        data = []
        for s in pickup_shipments:
            data.append({
                "ShipmentID": s.shipment_id,
                "Status": s.status,
                "Checked": s.checked,
                "Imported": s.imported,
                "InspectedDate": s.inspected_date
            })
        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="احفظ ملف بيانات البيك أب"
        )
        if not file_path:
            return
        try:
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("نجاح", "تم تصدير بيانات البيك أب بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تصدير البيانات: {e}")

    def import_pickup_data(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")],
            title="اختر ملف بيانات البيك أب للاستيراد"
        )
        if not file_path:
            return
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل قراءة الملف: {e}")
            return
        if "ShipmentID" not in df.columns:
            messagebox.showerror("خطأ", "ملف CSV غير صالح. العمود 'ShipmentID' مفقود.")
            return
        session = SessionLocal()
        try:
            for index, row in df.iterrows():
                shipment_id = str(row["ShipmentID"]).strip().lower()
                new_shipment = Shipment(
                    shipment_id=shipment_id,
                    status="Pickup",
                    checked=True,
                    imported=True,
                    employee_id=self.logged_in_user.id,
                    inspected_date=datetime.datetime.now(),
                    inspected_by=self.logged_in_user.id
                )
                session.add(new_shipment)
            session.commit()
            messagebox.showinfo("نجاح", "تم استيراد بيانات البيك أب بنجاح.")
            self.refresh_company_stats()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل استيراد البيانات: {e}")
        finally:
            session.close()

    def delete_all_shipments(self):
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع بيانات الشحنات؟"):
            return
        session = SessionLocal()
        try:
            deleted_count = session.query(Shipment).delete()
            session.commit()
            messagebox.showinfo("نجاح", f"تم حذف {deleted_count} من بيانات الشحنات.")
            self.refresh_company_stats()
            self.refresh_shipment_stats()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل حذف البيانات: {e}")
        finally:
            session.close()

    # ----------------------------
    def logout(self):
        self.destroy()
        from login import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()

    # ----------------------------
    def setup_right_click_menu(self):
        self.rc_menu = tk.Menu(self, tearoff=0)
        self.rc_menu.add_command(label="Mark as Checked", command=self.mark_selected_checked)
        self.rc_menu.add_command(label="Mark as Unchecked", command=self.mark_selected_unchecked)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id)
                self.rc_menu.post(event.x_root, event.y_root)
        finally:
            self.rc_menu.grab_release()

    def mark_selected_checked(self):
        selected = self.tree.focus()
        if selected:
            shipment_id = self.tree.item(selected)["values"][0]
            self.entry.delete(0, END)
            self.entry.insert(0, shipment_id)
            self.check_shipment()

    def mark_selected_unchecked(self):
        selected = self.tree.focus()
        if selected:
            shipment_id = self.tree.item(selected)["values"][0]
            for ship in self.current_shipments:
                if ship["ID"] == shipment_id:
                    ship["Checked"] = False
                    ship["inspected_date"] = None
                    break
            session = SessionLocal()
            db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id).order_by(Shipment.id.desc()).first()
            if db_shipment:
                db_shipment.checked = False
                db_shipment.inspected_date = None
                session.commit()
            session.close()
            self.update_treeview()
            self.update_remaining_text()
            messagebox.showinfo("نجاح", f"تم تعديل حالة الشحنة {shipment_id} إلى غير مفحوصة.")

    def setup_treeview_sorting(self):
        pass

    def treeview_sort_column(self, col, reverse):
        data_list = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            data_list.sort(key=lambda t: float(t[0]) if t[0].replace('.', '', 1).isdigit() else t[0], reverse=reverse)
        except Exception:
            data_list.sort(reverse=reverse)
        for index, (val, k) in enumerate(data_list):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def update_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in self.current_shipments:
            self.tree.insert("", "end", values=(s["ID"], s["Status"], s["Checked"]))

    def update_remaining_text(self):
        self.remaining_text.delete("1.0", "end")
        for s in self.current_shipments:
            if not s["Checked"]:
                self.remaining_text.insert("end", s["ID"] + "\n")

    def update_uploaded_count(self):
        count = len(self.current_shipments)
        if hasattr(self, 'uploaded_count_label'):
            self.uploaded_count_label.configure(
                text=self.translations[self.current_language]["uploaded_count"].format(count)
            )

    def play_sound(self, filename):
        try:
            sound_path = os.path.join(base_dir, filename)
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing sound: {e}")

    def check_shipment(self):
        shipment_id = self.entry.get().strip().lower()
        if not shipment_id:
            self.result_label.configure(text="الرجاء إدخال رقم الشحنة!", text_color="orange")
            return
        found_ship = None
        for ship in self.current_shipments:
            if ship["ID"] == shipment_id:
                found_ship = ship
                break
        session = SessionLocal()
        try:
            if found_ship:
                now = datetime.datetime.now()
                self.undo_stack.append({
                    "ID": shipment_id,
                    "previous_checked": found_ship["Checked"],
                    "previous_inspected_date": found_ship["inspected_date"]
                })
                found_ship["Checked"] = True
                found_ship["inspected_date"] = str(now)
                db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id)\
                                  .order_by(Shipment.id.desc()).first()
                if db_shipment:
                    db_shipment.checked = True
                    db_shipment.inspected_date = now
                    db_shipment.inspected_by = self.logged_in_user.id
                    session.commit()
                if found_ship["Status"] == "Line":
                    self.result_label.configure(text="Line - سيتم إعادة إرسال الشحنة!", text_color="green")
                    if not self.silent_line.get():
                        self.play_sound("line_sound.mp3")
                elif found_ship["Status"] == "Return":
                    self.result_label.configure(text="Return - سيتم إرجاع الشحنة!", text_color="red")
                    if not self.silent_return.get():
                        self.play_sound("return_sound.mp3")
                else:
                    self.result_label.configure(text=f"{found_ship['Status']} - حالة غير معروفة", text_color="orange")
            else:
                self.result_label.configure(text="لم يتم العثور على رقم الشحنة!", text_color="orange")
                self.unmatched_shipments.append(shipment_id)
                self.unmatched_text.insert("end", shipment_id + "\n")
                if not self.silent_unsimilar.get():
                    self.play_sound("unsimilar.mp3")
                new_unmatched = UnmatchedShipment(
                    shipment_id=shipment_id,
                    employee_id=self.logged_in_user.id
                )
                session.add(new_unmatched)
                session.commit()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الفحص: {e}")
        finally:
            session.close()
        self.after(50, lambda: (self.entry.delete(0, END), self.entry.focus_set()))
        self.update_treeview()
        self.update_remaining_text()

    def export_inspected_excel(self):
        if not self.current_shipments and not self.unmatched_shipments:
            messagebox.showwarning("تنبيه", "لا يوجد شحنات أو أرقام غير متطابقة للتصدير!")
            return
        unique_shipments = {}
        for s in self.current_shipments:
            unique_shipments[s["ID"]] = s
        data = []
        for s in unique_shipments.values():
            category = "مفحوص" if s["Checked"] else "متبقية"
            data.append({
                "ID": s["ID"],
                "Status": s["Status"],
                "Checked": s["Checked"],
                "Category": category
            })
        for uid in self.unmatched_shipments:
            data.append({
                "ID": uid,
                "Status": "غير متطابقة",
                "Checked": False,
                "Category": "غير متطابقة"
            })
        df_all = pd.DataFrame(data)
        default_name = "shipments_تم الفحص.xlsx"
        if self.imported_excel_path:
            base_name = os.path.splitext(os.path.basename(self.imported_excel_path))[0]
            default_name = base_name + "_تم الفحص.xlsx"
        export_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not export_path:
            return
        try:
            with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, sheet_name='تم الفحص', index=False)
                workbook = writer.book
                worksheet = writer.sheets['تم الفحص']
                nrows = len(df_all)
                if nrows > 0:
                    format_checked = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                    format_remaining = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
                    format_unmatched = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                    data_range = f"A2:D{nrows+1}"
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="مفحوص")',
                        'format': format_checked
                    })
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="متبقية")',
                        'format': format_remaining
                    })
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="غير متطابقة")',
                        'format': format_unmatched
                    })
                worksheet.write(nrows + 2, 0, "الموظف:")
                worksheet.write(nrows + 2, 1, self.logged_in_user.name)
            messagebox.showinfo("نجاح", "تم تصدير ملف Excel بنجاح!")
            self.current_shipments = []
            self.unmatched_shipments = []
            self.unmatched_text.delete("1.0", "end")
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تصدير ملف Excel: {e}")

    def export_report_pdf(self):
        pdf_file = os.path.join(os.getcwd(), "shipment_report.pdf")
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height-50, "Shipment Report")
        c.setFont("Helvetica", 12)
        textobject = c.beginText(40, height-100)
        for s in self.current_shipments:
            line = f"ID: {s['ID']} | Status: {s['Status']} | Checked: {s['Checked']}"
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()
        messagebox.showinfo("نجاح", f"تم حفظ التقرير في {pdf_file}")

    def search_shipment(self):
        shipment_id = ctk.CTkInputDialog(title="بحث عن شحنة", text="أدخل رقم الشحنة:").get_input()
        if not shipment_id:
            return
        shipment_id = shipment_id.strip().lower()
        found = None
        for s in self.current_shipments:
            if s["ID"] == shipment_id:
                found = s
                break
        if found:
            inspector_name = "غير محدد"
            if found["Checked"] and self.logged_in_user.name:
                inspector_name = self.logged_in_user.name
            details = f"تم الفحص: {'نعم' if found['Checked'] else 'لا'}\n"
            details += f"تاريخ الفحص: {found['inspected_date']}\n"
            details += f"تم الاستلام بواسطة: {inspector_name}"
            messagebox.showinfo("تفاصيل الشحنة", details)
        else:
            messagebox.showerror("الشحنة غير موجودة", "لم يتم العثور على الشحنة.")

    def filter_shipments(self, event):
        query = self.search_var.get().strip().lower()
        filtered = [s for s in self.current_shipments if query in s["ID"]]
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in filtered:
            self.tree.insert("", "end", values=(s["ID"], s["Status"], s["Checked"]))

    def update_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in self.current_shipments:
            self.tree.insert("", "end", values=(s["ID"], s["Status"], s["Checked"]))

    def update_remaining_text(self):
        self.remaining_text.delete("1.0", "end")
        for s in self.current_shipments:
            if not s["Checked"]:
                self.remaining_text.insert("end", s["ID"] + "\n")

    def update_uploaded_count(self):
        count = len(self.current_shipments)
        if hasattr(self, 'uploaded_count_label'):
            self.uploaded_count_label.configure(
                text=self.translations[self.current_language]["uploaded_count"].format(count)
            )

    def play_sound(self, filename):
        try:
            sound_path = os.path.join(base_dir, filename)
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing sound: {e}")

    def logout(self):
        self.destroy()
        from login import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()

    def sync_cached_shipments(self):
        cache = self.load_cached_shipments()
        if not cache:
            messagebox.showinfo("Info", "No offline shipments to sync.")
            return
        session = SessionLocal()
        try:
            for s in cache:
                new_ship = Shipment(
                    shipment_id=s["ID"],
                    status=s["Status"],
                    checked=s["Checked"],
                    employee_id=s["employee_id"],
                    imported=s.get("imported", True),
                    inspected_date=s.get("inspected_date")
                )
                session.add(new_ship)
            session.commit()
            with open(CACHE_FILE, "w") as f:
                json.dump([], f)
            messagebox.showinfo("نجاح", "تم مزامنة الشحنات غير المرسلة.")
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل المزامنة: {e}")
        finally:
            session.close()

    def save_shipment_to_cache(self, shipment_data):
        cache = self.load_cached_shipments()
        cache.append(shipment_data)
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f)
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")

    def load_cached_shipments(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading cache: {e}")
        return []

    def add_shipments(self):
        confirm = messagebox.askyesno("تأكيد", "هل تريد حفظ الشحنات؟")
        if not confirm:
            return
        line_ids = self.line_input_text.get("1.0", "end").strip().splitlines()
        return_ids = self.return_input_text.get("1.0", "end").strip().splitlines()
        session = SessionLocal()
        try:
            for lid in line_ids:
                lid = lid.strip().lower()
                if not lid:
                    continue
                shipment_record = {
                    "ID": lid,
                    "Status": "Line",
                    "Checked": False,
                    "inspected_date": None,
                    "employee_id": self.logged_in_user.id,
                    "imported": True
                }
                if self.offline_mode.get():
                    self.save_shipment_to_cache(shipment_record)
                else:
                    new_ship = Shipment(
                        shipment_id=lid,
                        status="Line",
                        checked=False,
                        employee_id=self.logged_in_user.id,
                        imported=True
                    )
                    session.add(new_ship)
                self.current_shipments.append(shipment_record)
            for rid in return_ids:
                rid = rid.strip().lower()
                if not rid:
                    continue
                shipment_record = {
                    "ID": rid,
                    "Status": "Return",
                    "Checked": False,
                    "inspected_date": None,
                    "employee_id": self.logged_in_user.id,
                    "imported": True
                }
                if self.offline_mode.get():
                    self.save_shipment_to_cache(shipment_record)
                else:
                    new_ship = Shipment(
                        shipment_id=rid,
                        status="Return",
                        checked=False,
                        employee_id=self.logged_in_user.id,
                        imported=True
                    )
                    session.add(new_ship)
                self.current_shipments.append(shipment_record)
            if not self.offline_mode.get():
                session.commit()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل حفظ الشحنات: {e}")
        finally:
            session.close()
        self.line_input_text.delete("1.0", "end")
        self.return_input_text.delete("1.0", "end")
        self.update_treeview()
        self.update_remaining_text()
        self.update_uploaded_count()

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            title="حدد ملف Excel",
            filetypes=[("ملفات Excel", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        try:
            df = pd.read_excel(file_path)
            expected = {"ID": ["رقم الشحنة", "Shipment ID", "ID"],
                        "Status": ["الحالة", "Status"]}
            mapping = {}
            for key, variants in expected.items():
                for variant in variants:
                    matches = difflib.get_close_matches(variant, df.columns, cutoff=0.6)
                    if matches:
                        mapping[matches[0]] = key
                        break
            if "ID" not in mapping.values() or "Status" not in mapping.values():
                messagebox.showerror("خطأ", "لم يتم العثور على الأعمدة المطلوبة في ملف Excel.")
                return
            df = df.rename(columns=mapping)
            df["ID"] = df["ID"].astype(str).str.lower()
            line_statuses = [s.strip() for s in self.line_status_entry.get().split(',') if s.strip()]
            return_statuses = [s.strip() for s in self.return_status_entry.get().split(',') if s.strip()]
            def map_status(x):
                s = str(x).strip()
                if s in return_statuses:
                    return "Return"
                elif s in line_statuses:
                    return "Line"
                else:
                    return s
            df["Status"] = df["Status"].apply(map_status)
            total = len(df)
            session = SessionLocal()
            import_count = 0
            try:
                for i, (_, row) in enumerate(df.iterrows()):
                    sid = str(row["ID"]).strip().lower()
                    status_str = str(row["Status"]).strip()
                    if not sid or sid in ["nan"] or not status_str or status_str in ["nan"]:
                        continue
                    shipment_record = {
                        "ID": sid,
                        "Status": status_str,
                        "Checked": False,
                        "inspected_date": None,
                        "employee_id": self.logged_in_user.id,
                        "imported": True
                    }
                    if self.offline_mode.get():
                        self.save_shipment_to_cache(shipment_record)
                    else:
                        new_shipment = Shipment(
                            shipment_id=sid,
                            status=status_str,
                            checked=False,
                            employee_id=self.logged_in_user.id,
                            imported=True
                        )
                        session.add(new_shipment)
                    self.current_shipments.append(shipment_record)
                    import_count += 1
                    progress = (i + 1) / total
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"{int(progress * 100)}%")
                    self.update_idletasks()
                if not self.offline_mode.get():
                    session.commit()
                self.imported_excel_path = file_path
                from models import EmployeeActivity
                activity = EmployeeActivity(
                    employee_id=self.logged_in_user.id,
                    sheet_name=os.path.basename(file_path),
                    shipment_count=import_count
                )
                session.add(activity)
                session.commit()
                messagebox.showinfo("نجاح", "تم استيراد ملف Excel بنجاح!")
            finally:
                session.close()
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في استيراد ملف Excel: {e}")
        finally:
            self.progress_bar.set(0)
            self.progress_label.configure(text="0%")

    def import_excel_with_selection(self):
        if not self.imported_excel_path:
            messagebox.showerror("خطأ", "لم يتم تحديد ملف أو تحميل أعمدته بعد.")
            return
        id_col = self.excel_id_column_var.get().strip()
        status_col = self.excel_status_column_var.get().strip()
        if not id_col or not status_col:
            messagebox.showerror("خطأ", "يرجى اختيار العمودين قبل الاستيراد.")
            return
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        try:
            df = pd.read_excel(self.imported_excel_path)
            if id_col not in df.columns or status_col not in df.columns:
                messagebox.showerror("خطأ", "الأعمدة المختارة غير موجودة في الملف.")
                return
            df[id_col] = df[id_col].astype(str).str.lower()
            line_statuses = [s.strip() for s in self.line_status_entry.get().split(',') if s.strip()]
            return_statuses = [s.strip() for s in self.return_status_entry.get().split(',') if s.strip()]
            def map_status(x):
                s = str(x).strip()
                if s in return_statuses:
                    return "Return"
                elif s in line_statuses:
                    return "Line"
                else:
                    return s
            total = len(df)
            session = SessionLocal()
            import_count = 0
            try:
                for i, (_, row) in enumerate(df.iterrows()):
                    sid = str(row[id_col]).strip().lower()
                    status_str = map_status(str(row[status_col]).strip())
                    if not sid or sid in ["nan"] or not status_str or status_str in ["nan"]:
                        continue
                    shipment_record = {
                        "ID": sid,
                        "Status": status_str,
                        "Checked": False,
                        "inspected_date": None,
                        "employee_id": self.logged_in_user.id,
                        "imported": True
                    }
                    if self.offline_mode.get():
                        self.save_shipment_to_cache(shipment_record)
                    else:
                        new_shipment = Shipment(
                            shipment_id=sid,
                            status=status_str,
                            checked=False,
                            employee_id=self.logged_in_user.id,
                            imported=True
                        )
                        session.add(new_shipment)
                    self.current_shipments.append(shipment_record)
                    import_count += 1
                    progress = (i + 1) / total
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"{int(progress * 100)}%")
                    self.update_idletasks()
                if not self.offline_mode.get():
                    session.commit()
                from models import EmployeeActivity
                activity = EmployeeActivity(
                    employee_id=self.logged_in_user.id,
                    sheet_name=os.path.basename(self.imported_excel_path),
                    shipment_count=import_count
                )
                session.add(activity)
                session.commit()
                messagebox.showinfo("نجاح", f"تم الاستيراد باستخدام الأعمدة المختارة ({id_col}, {status_col}) بنجاح!")
            finally:
                session.close()
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في استيراد ملف Excel بالأعمدة المختارة: {e}")
        finally:
            self.progress_bar.set(0)
            self.progress_label.configure(text="0%")

    def check_shipment(self):
        shipment_id = self.entry.get().strip().lower()
        if not shipment_id:
            self.result_label.configure(text="الرجاء إدخال رقم الشحنة!", text_color="orange")
            return
        found_ship = None
        for ship in self.current_shipments:
            if ship["ID"] == shipment_id:
                found_ship = ship
                break
        session = SessionLocal()
        try:
            if found_ship:
                now = datetime.datetime.now()
                self.undo_stack.append({
                    "ID": shipment_id,
                    "previous_checked": found_ship["Checked"],
                    "previous_inspected_date": found_ship["inspected_date"]
                })
                found_ship["Checked"] = True
                found_ship["inspected_date"] = str(now)
                db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id)\
                                  .order_by(Shipment.id.desc()).first()
                if db_shipment:
                    db_shipment.checked = True
                    db_shipment.inspected_date = now
                    db_shipment.inspected_by = self.logged_in_user.id
                    session.commit()
                if found_ship["Status"] == "Line":
                    self.result_label.configure(text="Line - سيتم إعادة إرسال الشحنة!", text_color="green")
                    if not self.silent_line.get():
                        self.play_sound("line_sound.mp3")
                elif found_ship["Status"] == "Return":
                    self.result_label.configure(text="Return - سيتم إرجاع الشحنة!", text_color="red")
                    if not self.silent_return.get():
                        self.play_sound("return_sound.mp3")
                else:
                    self.result_label.configure(text=f"{found_ship['Status']} - حالة غير معروفة", text_color="orange")
            else:
                self.result_label.configure(text="لم يتم العثور على رقم الشحنة!", text_color="orange")
                self.unmatched_shipments.append(shipment_id)
                self.unmatched_text.insert("end", shipment_id + "\n")
                if not self.silent_unsimilar.get():
                    self.play_sound("unsimilar.mp3")
                new_unmatched = UnmatchedShipment(
                    shipment_id=shipment_id,
                    employee_id=self.logged_in_user.id
                )
                session.add(new_unmatched)
                session.commit()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الفحص: {e}")
        finally:
            session.close()
        self.after(50, lambda: (self.entry.delete(0, END), self.entry.focus_set()))
        self.update_treeview()
        self.update_remaining_text()

    def export_inspected_excel(self):
        if not self.current_shipments and not self.unmatched_shipments:
            messagebox.showwarning("تنبيه", "لا يوجد شحنات أو أرقام غير متطابقة للتصدير!")
            return
        unique_shipments = {}
        for s in self.current_shipments:
            unique_shipments[s["ID"]] = s
        data = []
        for s in unique_shipments.values():
            category = "مفحوص" if s["Checked"] else "متبقية"
            data.append({
                "ID": s["ID"],
                "Status": s["Status"],
                "Checked": s["Checked"],
                "Category": category
            })
        for uid in self.unmatched_shipments:
            data.append({
                "ID": uid,
                "Status": "غير متطابقة",
                "Checked": False,
                "Category": "غير متطابقة"
            })
        df_all = pd.DataFrame(data)
        default_name = "shipments_تم الفحص.xlsx"
        if self.imported_excel_path:
            base_name = os.path.splitext(os.path.basename(self.imported_excel_path))[0]
            default_name = base_name + "_تم الفحص.xlsx"
        export_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not export_path:
            return
        try:
            with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, sheet_name='تم الفحص', index=False)
                workbook = writer.book
                worksheet = writer.sheets['تم الفحص']
                nrows = len(df_all)
                if nrows > 0:
                    format_checked = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                    format_remaining = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
                    format_unmatched = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                    data_range = f"A2:D{nrows+1}"
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="مفحوص")',
                        'format': format_checked
                    })
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="متبقية")',
                        'format': format_remaining
                    })
                    worksheet.conditional_format(data_range, {
                        'type': 'formula',
                        'criteria': '=($D2="غير متطابقة")',
                        'format': format_unmatched
                    })
                worksheet.write(nrows + 2, 0, "الموظف:")
                worksheet.write(nrows + 2, 1, self.logged_in_user.name)
            messagebox.showinfo("نجاح", "تم تصدير ملف Excel بنجاح!")
            self.current_shipments = []
            self.unmatched_shipments = []
            self.unmatched_text.delete("1.0", "end")
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تصدير ملف Excel: {e}")

    def export_report_pdf(self):
        pdf_file = os.path.join(os.getcwd(), "shipment_report.pdf")
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height-50, "Shipment Report")
        c.setFont("Helvetica", 12)
        textobject = c.beginText(40, height-100)
        for s in self.current_shipments:
            line = f"ID: {s['ID']} | Status: {s['Status']} | Checked: {s['Checked']}"
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()
        messagebox.showinfo("نجاح", f"تم حفظ التقرير في {pdf_file}")

    def search_shipment(self):
        shipment_id = ctk.CTkInputDialog(title="بحث عن شحنة", text="أدخل رقم الشحنة:", font=self.font_cairo_16).get_input()
        if not shipment_id:
            return
        shipment_id = shipment_id.strip().lower()
        found = None
        for s in self.current_shipments:
            if s["ID"] == shipment_id:
                found = s
                break
        if found:
            inspector_name = "غير محدد"
            if found["Checked"] and self.logged_in_user.name:
                inspector_name = self.logged_in_user.name
            details = f"تم الفحص: {'نعم' if found['Checked'] else 'لا'}\n"
            details += f"تاريخ الفحص: {found['inspected_date']}\n"
            details += f"تم الاستلام بواسطة: {inspector_name}"
            messagebox.showinfo("تفاصيل الشحنة", details)
        else:
            messagebox.showerror("الشحنة غير موجودة", "لم يتم العثور على الشحنة.")

    def update_language(self):
        self.title(self.translations[self.current_language]["title"])
        if hasattr(self, 'uploaded_count_label'):
            self.uploaded_count_label.configure(
                text=self.translations[self.current_language]["uploaded_count"].format(len(self.current_shipments))
            )
        if hasattr(self, 'add_title_label'):
            self.add_title_label.configure(text=self.translations[self.current_language]["add_shipments"])
        if hasattr(self, 'line_label'):
            self.line_label.configure(text=self.translations[self.current_language]["line_shipments"])
        if hasattr(self, 'return_label'):
            self.return_label.configure(text=self.translations[self.current_language]["return_shipments"])
        if hasattr(self, 'save_btn'):
            self.save_btn.configure(text=self.translations[self.current_language]["save_shipments"])
        if hasattr(self, 'check_title_label'):
            self.check_title_label.configure(text=self.translations[self.current_language]["check_shipment"])
        if hasattr(self, 'entry_label'):
            self.entry_label.configure(text=self.translations[self.current_language]["enter_shipment_id"])
        if hasattr(self, 'check_btn'):
            self.check_btn.configure(text=self.translations[self.current_language]["check_shipment"])
        if hasattr(self, 'clear_btn'):
            self.clear_btn.configure(text=self.translations[self.current_language]["clear_shipments"])
        if hasattr(self, 'unmatched_title_label'):
            self.unmatched_title_label.configure(text=self.translations[self.current_language]["unmatched"])
        if hasattr(self, 'table_title_label'):
            self.table_title_label.configure(text=self.translations[self.current_language]["all_shipments"])
        if hasattr(self, 'remaining_title_label'):
            self.remaining_title_label.configure(text=self.translations[self.current_language]["remaining"])
        if hasattr(self, 'import_btn'):
            self.import_btn.configure(text=self.translations[self.current_language]["import_excel"])
        if hasattr(self, 'export_btn'):
            self.export_btn.configure(text=self.translations[self.current_language]["export_inspected"])
        if hasattr(self, 'print_report_btn'):
            self.print_report_btn.configure(text=self.translations[self.current_language]["print_report"])
        if hasattr(self, 'col_settings_title'):
            self.col_settings_title.configure(text=self.translations[self.current_language]["excel_columns_settings"])
        if hasattr(self, 'load_cols_btn'):
            self.load_cols_btn.configure(text=self.translations[self.current_language]["excel_load_columns"])
        if hasattr(self, 'id_col_label'):
            self.id_col_label.configure(text=self.translations[self.current_language]["select_id_column"])
        if hasattr(self, 'status_col_label'):
            self.status_col_label.configure(text=self.translations[self.current_language]["select_status_column"])
        if hasattr(self, 'import_selected_btn'):
            self.import_selected_btn.configure(text=self.translations[self.current_language]["excel_import_with_selection"])
        if hasattr(self, 'status_title'):
            self.status_title.configure(text=self.translations[self.current_language]["excel_status_settings"])
        if hasattr(self, 'line_status_label'):
            self.line_status_label.configure(text=self.translations[self.current_language]["line_statuses"])
        if hasattr(self, 'return_status_label'):
            self.return_status_label.configure(text=self.translations[self.current_language]["return_statuses"])
        if hasattr(self, 'search_btn'):
            self.search_btn.configure(text=self.translations[self.current_language]["search_shipment"])
        if hasattr(self, 'live_search_label'):
            self.live_search_label.configure(text=self.translations[self.current_language]["live_search"])
        if hasattr(self, 'offline_chk_box'):
            self.offline_chk_box.configure(text=self.translations[self.current_language]["offline_mode"])
        if hasattr(self, 'sync_btn'):
            self.sync_btn.configure(text=self.translations[self.current_language]["sync_offline"])
        if hasattr(self, 'undo_btn'):
            self.undo_btn.configure(text=self.translations[self.current_language]["undo"])
        if hasattr(self, 'theme_btn'):
            self.theme_btn.configure(text=self.translations[self.current_language]["toggle_theme"])
        if hasattr(self, 'fs_btn'):
            self.fs_btn.configure(text=self.translations[self.current_language]["toggle_fullscreen"])
        if hasattr(self, 'dashboard_btn'):
            self.dashboard_btn.configure(text=self.translations[self.current_language]["dashboard_tab"])
        if hasattr(self, 'search_btn'):
            self.search_btn.configure(text=self.translations[self.current_language]["search_tab"])
        if hasattr(self, 'excel_btn'):
            self.excel_btn.configure(text=self.translations[self.current_language]["excel_tab"])
        if hasattr(self, 'settings_btn'):
            self.settings_btn.configure(text=self.translations[self.current_language]["settings_tab"])

    def change_language(self, selection):
        if selection == "العربية":
            self.current_language = "ar"
        else:
            self.current_language = "en"
        self.update_language()

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)

    def toggle_fullscreen(self):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    def set_window_geometry(self):
        w, h = 1200, 800
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        cx = int(sw / 2 - w / 2)
        cy = int(sh / 2 - h / 2)
        self.geometry(f"{w}x{h}+{cx}+{cy}")

    def init_pygame(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            logging.error(f"Error initializing pygame mixer: {e}")

    def open_excel_settings(self):
        # Open the Excel Settings window (implemented in a separate file)
        from excel_settings import ExcelSettingsWindow
        excel_win = ExcelSettingsWindow(self)
        excel_win.grab_set()

if __name__ == "__main__":
    class DummyUser:
        def __init__(self):
            self.name = "مدير تجريبي"
            self.id = 888
            self.role = "manager"
            self.company_id = 1
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ManagerDashboard(DummyUser())
    app.mainloop()
