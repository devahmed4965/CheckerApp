import os
import sys
import json
import difflib
import logging
import datetime
import pandas as pd
import pygame
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, END
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from models import SessionLocal, Shipment, EmployeeActivity, Employee, UnmatchedShipment, Company

# ----------------------------------------------------------------------------------------
# 1) Define new color palette and simple animation helpers
# ----------------------------------------------------------------------------------------
PRIMARY_COLOR = "#2D2D2D"        # Header background
SECONDARY_COLOR = "#383838"      # Main frames background
BUTTON_COLOR = "#4C4C4C"         # Normal button color
BUTTON_HOVER_COLOR = "#5E5E5E"   # Hover color
TEXT_COLOR = "#FFFFFF"           # White text for contrast

def on_button_enter(event):
    try:
        event.widget.configure(fg_color=BUTTON_HOVER_COLOR)
    except Exception:
        pass

def on_button_leave(event):
    try:
        event.widget.configure(fg_color=BUTTON_COLOR)
    except Exception:
        pass

def fade_in_window(tk_window, increment=0.05, delay=10):
    alpha = 0.0
    tk_window.attributes("-alpha", alpha)
    while alpha < 1.0:
        alpha += increment
        if alpha > 1.0:
            alpha = 1.0
        tk_window.attributes("-alpha", alpha)
        tk_window.update()
        tk_window.after(delay)

# ----------------------------------------------------------------------------------------
# Determine base directory for resource loading
# ----------------------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Offline cache file location
CACHE_FILE = os.path.join(base_dir, "offline_shipments_cache.json")

# Configure logging
logging.basicConfig(
    filename=os.path.join(base_dir, 'shipment_app.log'),
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ----------------------------------------------------------------------------------------
# Excel Settings Window for updating Excel configuration in the Company table
# ----------------------------------------------------------------------------------------
class ExcelSettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("إعدادات Excel")
        self.geometry("500x400")
        self.parent = parent
        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.excel_columns_list = []

        # Columns settings frame
        self.columns_frame = ctk.CTkFrame(self)
        self.columns_frame.pack(pady=10, padx=10, fill="x")
        self.label_columns = ctk.CTkLabel(self.columns_frame, text="إعدادات الأعمدة", font=self.font_cairo_16)
        self.label_columns.pack(pady=5)
        self.load_columns_btn = ctk.CTkButton(self.columns_frame, text="تحميل أعمدة الملف", command=self.load_excel_columns, font=self.font_cairo_16)
        self.load_columns_btn.pack(pady=5)
        self.id_col_label = ctk.CTkLabel(self.columns_frame, text="اختر عمود رقم الشحنة", font=self.font_cairo_16)
        self.id_col_label.pack(pady=5)
        self.id_col_combobox = ctk.CTkComboBox(self.columns_frame, values=[], font=self.font_cairo_16)
        self.id_col_combobox.pack(pady=5)
        self.status_col_label = ctk.CTkLabel(self.columns_frame, text="اختر عمود الحالة", font=self.font_cairo_16)
        self.status_col_label.pack(pady=5)
        self.status_col_combobox = ctk.CTkComboBox(self.columns_frame, values=[], font=self.font_cairo_16)
        self.status_col_combobox.pack(pady=5)

        # Status settings frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=10, padx=10, fill="x")
        self.label_status = ctk.CTkLabel(self.status_frame, text="إعدادات الحالات", font=self.font_cairo_16)
        self.label_status.pack(pady=5)
        self.line_status_label = ctk.CTkLabel(self.status_frame, text="حالات Line (مفصولة بفواصل):", font=self.font_cairo_16)
        self.line_status_label.pack(pady=5)
        self.line_status_entry = ctk.CTkEntry(self.status_frame, font=self.font_cairo_16)
        self.line_status_entry.pack(pady=5)
        self.return_status_label = ctk.CTkLabel(self.status_frame, text="حالات Return (مفصولة بفواصل):", font=self.font_cairo_16)
        self.return_status_label.pack(pady=5)
        self.return_status_entry = ctk.CTkEntry(self.status_frame, font=self.font_cairo_16)
        self.return_status_entry.pack(pady=5)

        # Save button
        self.save_btn = ctk.CTkButton(self, text="حفظ الإعدادات", command=self.save_settings, font=self.font_cairo_16)
        self.save_btn.pack(pady=10)

    def load_excel_columns(self):
        file_path = filedialog.askopenfilename(
            title="حدد ملف Excel",
            filetypes=[("ملفات Excel", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path, nrows=1)
            self.excel_columns_list = list(df.columns)
            self.id_col_combobox.configure(values=self.excel_columns_list)
            self.status_col_combobox.configure(values=self.excel_columns_list)
            messagebox.showinfo("نجاح", "تم تحميل الأعمدة بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في قراءة ملف Excel: {e}")

    def save_settings(self):
        excel_id = self.id_col_combobox.get().strip()
        excel_status = self.status_col_combobox.get().strip()
        line_statuses = self.line_status_entry.get().strip()
        return_statuses = self.return_status_entry.get().strip()

        if not excel_id or not excel_status:
            messagebox.showerror("خطأ", "يرجى اختيار عمود رقم الشحنة وعمود الحالة.")
            return

        session = SessionLocal()
        try:
            # Update the Company record for the current user's company.
            company = session.query(Company).filter_by(id=self.parent.logged_in_user.company_id).first()
            if company:
                company.excel_id_column = excel_id
                company.excel_status_column = excel_status
                company.excel_line_statuses = line_statuses
                company.excel_return_statuses = return_statuses
                session.commit()
                messagebox.showinfo("نجاح", "تم حفظ إعدادات Excel بنجاح.")
            else:
                messagebox.showerror("خطأ", "لم يتم العثور على الشركة.")
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات: {e}")
        finally:
            session.close()
            self.destroy()

# ----------------------------------------------------------------------------------------
# Main Employee Dashboard (Shipment Checker)
# ----------------------------------------------------------------------------------------
class ShipmentCheckerApp(ctk.CTk):
    def __init__(self, logged_in_user):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.title(f"شاشة الشحنات - {logged_in_user.name} (موظف)")
        self.set_window_geometry()
        self.init_pygame()

        # Local data
        self.current_shipments = []
        self.unmatched_shipments = []
        self.undo_stack = []

        self.offline_mode = ctk.BooleanVar(value=False)
        self.silent_line = ctk.BooleanVar(value=False)
        self.silent_return = ctk.BooleanVar(value=False)
        self.silent_unsimilar = ctk.BooleanVar(value=False)

        self.imported_excel_path = None
        self.excel_id_column_var = ctk.StringVar(value="")
        self.excel_status_column_var = ctk.StringVar(value="")
        self.excel_columns_list = []

        # Multi-language support
        self.current_language = "ar"
        self.translations = {
            "ar": {
                "title": f"شاشة الشحنات - {logged_in_user.name} (موظف)",
                "dashboard_tab": "لوحة المعلومات",
                "excel_tab": "إعدادات Excel",
                "search_tab": "البحث",
                "settings_tab": "الإعدادات",
                "logout": "تسجيل الخروج",
                "uploaded_count": "الشحنات المرفوعة: {}",
                "add_shipments": "إضافة الشحنات",
                "line_shipments": "شحنات Line:",
                "return_shipments": "شحنات Return:",
                "save_shipments": "حفظ الشحنات",
                "check_shipment": "فحص الشحنة",
                "enter_shipment_id": "أدخل رقم الشحنة:",
                "clear_shipments": "مسح جميع الشحنات",
                "unmatched": "الأرقام غير المتطابقة",
                "all_shipments": "جميع الشحنات",
                "remaining": "الشحنات المتبقية",
                "sound_settings": "إعدادات الصوت",
                "offline_mode": "الوضع دون اتصال",
                "sync_offline": "مزامنة الشحنات غير المرسلة",
                "undo": "تراجع",
                "print_report": "طباعة التقرير",
                "import_excel": "استيراد Excel",
                "export_inspected": "تم الفحص",
                "live_search": "بحث مباشر:",
                "search_shipment": "بحث عن شحنة",
                "toggle_theme": "تبديل الوضع الداكن",
                "toggle_fullscreen": "تعبئة الشاشة",
                "excel_columns_settings": "إعدادات الأعمدة",
                "excel_load_columns": "تحميل أعمدة الملف",
                "excel_import_with_selection": "استيراد بالأعمدة المختارة",
                "select_id_column": "اختر عمود رقم الشحنة",
                "select_status_column": "اختر عمود الحالة",
                "excel_status_settings": "إعدادات الحالات",
                "line_statuses": "حالات Line (مفصولة بفواصل):",
                "return_statuses": "حالات Return (مفصولة بفواصل):",
            },
            "en": {
                "title": f"Shipments Screen - {logged_in_user.name} (Employee)",
                "dashboard_tab": "Dashboard",
                "excel_tab": "Excel",
                "search_tab": "Search",
                "settings_tab": "Settings",
                "logout": "Logout",
                "uploaded_count": "Uploaded Shipments: {}",
                "add_shipments": "Add Shipments",
                "line_shipments": "Line Shipments:",
                "return_shipments": "Return Shipments:",
                "save_shipments": "Save Shipments",
                "check_shipment": "Check Shipment",
                "enter_shipment_id": "Enter Shipment ID:",
                "clear_shipments": "Clear All Shipments",
                "unmatched": "Unmatched Numbers",
                "all_shipments": "All Shipments",
                "remaining": "Remaining Shipments",
                "sound_settings": "Sound Settings",
                "offline_mode": "Offline Mode",
                "sync_offline": "Sync Offline Shipments",
                "undo": "Undo",
                "print_report": "Print Report",
                "import_excel": "Import Excel",
                "export_inspected": "Export Inspected",
                "live_search": "Live Search:",
                "search_shipment": "Search Shipment",
                "toggle_theme": "Toggle Dark Mode",
                "toggle_fullscreen": "Toggle Full Screen",
                "excel_columns_settings": "Excel Column Settings",
                "excel_load_columns": "Load Columns",
                "excel_import_with_selection": "Import with Selected Columns",
                "select_id_column": "Select Shipment ID Column",
                "select_status_column": "Select Status Column",
                "excel_status_settings": "Status Settings",
                "line_statuses": "Line Statuses (comma-separated):",
                "return_statuses": "Return Statuses (comma-separated):",
            }
        }

        # Define fonts
        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.font_cairo_18_bold = ctk.CTkFont(family="Cairo", size=18, weight="bold")
        self.font_cairo_24_bold = ctk.CTkFont(family="Cairo", size=24, weight="bold")

        # Create main frames and Tabview
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=1200, height=800, fg_color=SECONDARY_COLOR)
        self.tabview = ctk.CTkTabview(self.scrollable_frame, corner_radius=0, width=1200, height=700)
        self.tabview._segmented_button.pack_forget()

        self.tabview.add("dashboard")
        self.tabview.add("excel")
        self.tabview.add("search")
        self.tabview.add("settings")

        self.dashboard_tab = self.tabview.tab("dashboard")
        self.excel_tab = self.tabview.tab("excel")
        self.search_tab = self.tabview.tab("search")
        self.settings_tab = self.tabview.tab("settings")

        # Create the header bar for navigation
        self.create_header_bar()

        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.pack(fill="both", expand=True)

        # Build UI inside each tab
        self.build_dashboard_tab()
        self.build_excel_tab()
        self.build_search_tab()
        self.build_settings_tab()

        self.setup_right_click_menu()
        self.setup_treeview_sorting()

        self.update_treeview()
        self.update_remaining_text()
        self.update_uploaded_count()
        self.update_language()

        self.after(100, lambda: fade_in_window(self))

    def create_header_bar(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=PRIMARY_COLOR)
        header.pack(side="top", fill="x")
        nav_frame = ctk.CTkFrame(header, fg_color=PRIMARY_COLOR)
        nav_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        button_params = {
            "font": self.font_cairo_16,
            "fg_color": BUTTON_COLOR,
            "hover_color": BUTTON_HOVER_COLOR,
            "text_color": TEXT_COLOR,
            "border_width": 1,
            "border_color": "#454545",
            "corner_radius": 6,
            "width": 120
        }
        self.dashboard_btn = ctk.CTkButton(
            nav_frame,
            text=self.translations[self.current_language]["dashboard_tab"],
            command=lambda: self.tabview.set("dashboard"),
            **button_params
        )
        self.dashboard_btn.pack(side="left", padx=5, pady=0)
        self.dashboard_btn.bind("<Enter>", on_button_enter)
        self.dashboard_btn.bind("<Leave>", on_button_leave)
        self.search_btn = ctk.CTkButton(
            nav_frame,
            text=self.translations[self.current_language]["search_tab"],
            command=lambda: self.tabview.set("search"),
            **button_params
        )
        self.search_btn.pack(side="left", padx=5, pady=0)
        self.search_btn.bind("<Enter>", on_button_enter)
        self.search_btn.bind("<Leave>", on_button_leave)
        self.excel_btn = ctk.CTkButton(
            nav_frame,
            text=self.translations[self.current_language]["excel_tab"],
            command=lambda: self.tabview.set("excel"),
            **button_params
        )
        self.excel_btn.pack(side="left", padx=5, pady=0)
        self.excel_btn.bind("<Enter>", on_button_enter)
        self.excel_btn.bind("<Leave>", on_button_leave)
        self.settings_btn = ctk.CTkButton(
            nav_frame,
            text=self.translations[self.current_language]["settings_tab"],
            command=lambda: self.tabview.set("settings"),
            **button_params
        )
        self.settings_btn.pack(side="left", padx=5, pady=0)
        self.settings_btn.bind("<Enter>", on_button_enter)
        self.settings_btn.bind("<Leave>", on_button_leave)
        right_frame = ctk.CTkFrame(header, fg_color=PRIMARY_COLOR)
        right_frame.pack(side="right", padx=10, pady=10)
        self.language_var = ctk.StringVar(value="العربية")
        lang_cb = ctk.CTkComboBox(
            right_frame,
            values=["العربية", "English"],
            variable=self.language_var,
            font=self.font_cairo_16,
            width=100,
            command=self.change_language
        )
        lang_cb.pack(side="right", padx=10)
        logout_btn = ctk.CTkButton(
            right_frame,
            text=self.translations[self.current_language]["logout"],
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR,
            border_width=1,
            border_color="#1F1F1F",
            corner_radius=6,
            command=self.logout,
            width=100
        )
        logout_btn.pack(side="right", padx=10)
        logout_btn.bind("<Enter>", on_button_enter)
        logout_btn.bind("<Leave>", on_button_leave)

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

    def build_dashboard_tab(self):
        row0_frame = ctk.CTkFrame(self.dashboard_tab, fg_color=SECONDARY_COLOR)
        row0_frame.pack(fill="x", padx=10, pady=10)
        self.uploaded_count_label = ctk.CTkLabel(row0_frame, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.uploaded_count_label.pack(side="left", padx=10)
        row1_frame = ctk.CTkFrame(self.dashboard_tab, fg_color=SECONDARY_COLOR)
        row1_frame.pack(fill="x", padx=10, pady=10)
        add_card = ctk.CTkFrame(row1_frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        add_card.pack(side="left", fill="both", expand=True, padx=5)
        self.add_title_label = ctk.CTkLabel(add_card, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.add_title_label.pack(pady=5)
        self.line_label = ctk.CTkLabel(add_card, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.line_label.pack(pady=2)
        self.line_input_text = ctk.CTkTextbox(add_card, height=80, font=self.font_cairo_16)
        self.line_input_text.pack(padx=10, pady=5, fill="x")
        self.return_label = ctk.CTkLabel(add_card, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.return_label.pack(pady=2)
        self.return_input_text = ctk.CTkTextbox(add_card, height=80, font=self.font_cairo_16)
        self.return_input_text.pack(padx=10, pady=5, fill="x")
        self.save_btn = ctk.CTkButton(
            add_card,
            text="",
            command=self.add_shipments,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.save_btn.pack(pady=10)
        self.save_btn.bind("<Enter>", on_button_enter)
        self.save_btn.bind("<Leave>", on_button_leave)
        check_card = ctk.CTkFrame(row1_frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        check_card.pack(side="left", fill="both", expand=True, padx=5)
        self.check_title_label = ctk.CTkLabel(check_card, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.check_title_label.pack(pady=5)
        self.entry_label = ctk.CTkLabel(check_card, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.entry_label.pack(pady=2)
        self.entry = ctk.CTkEntry(check_card, width=250, font=self.font_cairo_16)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", lambda e: self.check_shipment())
        self.check_btn = ctk.CTkButton(
            check_card,
            text="",
            command=self.check_shipment,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.check_btn.pack(pady=5)
        self.check_btn.bind("<Enter>", on_button_enter)
        self.check_btn.bind("<Leave>", on_button_leave)
        self.result_label = ctk.CTkLabel(check_card, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.result_label.pack(pady=5)
        self.clear_btn = ctk.CTkButton(
            check_card,
            text="",
            command=self.clear_shipments,
            fg_color="red",
            hover_color="#ff4d4d",
            font=self.font_cairo_16,
            text_color=TEXT_COLOR
        )
        self.clear_btn.pack(pady=10)
        row2_frame = ctk.CTkFrame(self.dashboard_tab, fg_color=SECONDARY_COLOR)
        row2_frame.pack(fill="both", expand=True, padx=10, pady=10)
        unmatched_card = ctk.CTkFrame(row2_frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        unmatched_card.pack(side="left", fill="both", expand=True, padx=5)
        self.unmatched_title_label = ctk.CTkLabel(unmatched_card, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.unmatched_title_label.pack(pady=5)
        self.unmatched_text = ctk.CTkTextbox(unmatched_card, height=120, font=self.font_cairo_16)
        self.unmatched_text.pack(padx=10, pady=10, fill="both", expand=True)
        right_card = ctk.CTkFrame(row2_frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        right_card.pack(side="left", fill="both", expand=True, padx=5)
        self.table_title_label = ctk.CTkLabel(right_card, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.table_title_label.pack(pady=5)
        self.tree_frame = ctk.CTkFrame(right_card, fg_color=SECONDARY_COLOR)
        self.tree_frame.pack(pady=5, fill="both", expand=True)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("ID", "Status", "Checked"),
            show="headings",
            height=8
        )
        self.tree.heading("ID", text="رقم الشحنة", command=lambda: self.treeview_sort_column("ID", False))
        self.tree.heading("Status", text="الحالة", command=lambda: self.treeview_sort_column("Status", False))
        self.tree.heading("Checked", text="مفحوصة؟", command=lambda: self.treeview_sort_column("Checked", False))
        self.tree.pack(side="left", fill="both", expand=True)
        style = ttk.Style()
        style.configure("Treeview", font=("Cairo", 10))
        style.configure("Treeview.Heading", font=("Cairo", 16, "bold"))
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")
        self.tree.focus_set()
        remaining_card = ctk.CTkFrame(right_card, corner_radius=10, fg_color=SECONDARY_COLOR)
        remaining_card.pack(pady=10, fill="both", expand=True)
        self.remaining_title_label = ctk.CTkLabel(remaining_card, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.remaining_title_label.pack(pady=5)
        self.remaining_text = ctk.CTkTextbox(remaining_card, height=200, font=self.font_cairo_16)
        self.remaining_text.pack(padx=10, pady=10, fill="both", expand=True)

    def build_excel_tab(self):
        frame = ctk.CTkFrame(self.excel_tab, fg_color=SECONDARY_COLOR)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.progress_bar = ctk.CTkProgressBar(frame, width=300)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.progress_label = ctk.CTkLabel(frame, text="0%", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.progress_label.pack(pady=5)
        self.import_btn = ctk.CTkButton(
            frame,
            text="",
            command=self.import_excel,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.import_btn.pack(pady=10)
        self.import_btn.bind("<Enter>", on_button_enter)
        self.import_btn.bind("<Leave>", on_button_leave)
        self.export_btn = ctk.CTkButton(
            frame,
            text="",
            command=self.export_inspected_excel,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.export_btn.pack(pady=10)
        self.export_btn.bind("<Enter>", on_button_enter)
        self.export_btn.bind("<Leave>", on_button_leave)
        self.print_report_btn = ctk.CTkButton(
            frame,
            text="",
            command=self.export_report_pdf,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.print_report_btn.pack(pady=10)
        self.print_report_btn.bind("<Enter>", on_button_enter)
        self.print_report_btn.bind("<Leave>", on_button_leave)
        columns_settings_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        columns_settings_frame.pack(pady=20, fill="x")
        self.col_settings_title = ctk.CTkLabel(columns_settings_frame, text="", font=self.font_cairo_18_bold, text_color=TEXT_COLOR)
        self.col_settings_title.pack(pady=5)
        self.load_cols_btn = ctk.CTkButton(
            columns_settings_frame,
            text="",
            font=self.font_cairo_16,
            command=self.load_excel_columns,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.load_cols_btn.pack(pady=5)
        self.load_cols_btn.bind("<Enter>", on_button_enter)
        self.load_cols_btn.bind("<Leave>", on_button_leave)
        self.id_col_label = ctk.CTkLabel(columns_settings_frame, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.id_col_label.pack(pady=2)
        self.id_col_combobox = ctk.CTkComboBox(
            columns_settings_frame,
            values=[],
            variable=self.excel_id_column_var,
            font=self.font_cairo_16,
            width=250
        )
        self.id_col_combobox.pack(pady=2)
        self.status_col_label = ctk.CTkLabel(columns_settings_frame, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.status_col_label.pack(pady=2)
        self.status_col_combobox = ctk.CTkComboBox(
            columns_settings_frame,
            values=[],
            variable=self.excel_status_column_var,
            font=self.font_cairo_16,
            width=250
        )
        self.status_col_combobox.pack(pady=2)
        self.import_selected_btn = ctk.CTkButton(
            columns_settings_frame,
            text="",
            command=self.import_excel_with_selection,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.import_selected_btn.pack(pady=10)
        self.import_selected_btn.bind("<Enter>", on_button_enter)
        self.import_selected_btn.bind("<Leave>", on_button_leave)
        status_settings_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        status_settings_frame.pack(pady=20, fill="x")
        self.status_title = ctk.CTkLabel(
            status_settings_frame,
            text=self.translations[self.current_language]["excel_status_settings"],
            font=self.font_cairo_18_bold,
            text_color=TEXT_COLOR
        )
        self.status_title.pack(pady=5)
        self.line_status_label = ctk.CTkLabel(
            status_settings_frame,
            text=self.translations[self.current_language]["line_statuses"],
            font=self.font_cairo_16,
            text_color=TEXT_COLOR
        )
        self.line_status_label.pack(pady=5)
        self.line_status_entry = ctk.CTkEntry(status_settings_frame, width=300, font=self.font_cairo_16)
        self.line_status_entry.pack(pady=5)
        self.return_status_label = ctk.CTkLabel(
            status_settings_frame,
            text=self.translations[self.current_language]["return_statuses"],
            font=self.font_cairo_16,
            text_color=TEXT_COLOR
        )
        self.return_status_label.pack(pady=5)
        self.return_status_entry = ctk.CTkEntry(status_settings_frame, width=300, font=self.font_cairo_16)
        self.return_status_entry.pack(pady=5)

    def load_excel_columns(self):
        file_path = filedialog.askopenfilename(
            title="حدد ملف Excel لاستخراج الأعمدة",
            filetypes=[("ملفات Excel", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path, nrows=1)
            self.excel_columns_list = list(df.columns)
            self.id_col_combobox.configure(values=self.excel_columns_list)
            self.status_col_combobox.configure(values=self.excel_columns_list)
            self.imported_excel_path = file_path
            messagebox.showinfo("نجاح", "تم تحميل الأعمدة بنجاح. اختر العمودين من القوائم المنسدلة.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في قراءة ملف Excel: {e}")

    def build_search_tab(self):
        frame = ctk.CTkFrame(self.search_tab, fg_color=SECONDARY_COLOR)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.search_btn = ctk.CTkButton(
            frame,
            text="",
            command=self.search_shipment,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.search_btn.pack(pady=10)
        self.search_btn.bind("<Enter>", on_button_enter)
        self.search_btn.bind("<Leave>", on_button_leave)
        self.live_search_label = ctk.CTkLabel(frame, text="", font=self.font_cairo_16, text_color=TEXT_COLOR)
        self.live_search_label.pack(pady=10)
        self.search_var = ctk.StringVar()
        live_search_entry = ctk.CTkEntry(frame, textvariable=self.search_var, font=self.font_cairo_16, width=250)
        live_search_entry.pack(pady=5)
        live_search_entry.bind("<KeyRelease>", self.filter_shipments)

    def build_settings_tab(self):
        frame = ctk.CTkFrame(self.settings_tab, fg_color=SECONDARY_COLOR)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        # زر فتح نافذة مهام الأوبريشن
        operation_tasks_btn = ctk.CTkButton(
            frame,
            text="مهام الأوبريشن",
            command=self.open_operation_tasks,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        operation_tasks_btn.pack(pady=10)
        self.offline_chk_box = ctk.CTkCheckBox(
            frame,
            text=self.translations[self.current_language]["offline_mode"],
            variable=self.offline_mode,
            font=self.font_cairo_16,
            text_color=TEXT_COLOR,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            border_color="#666666"
        )
        self.offline_chk_box.pack(pady=10)
        self.sync_btn = ctk.CTkButton(
            frame,
            text=self.translations[self.current_language]["sync_offline"],
            command=self.sync_cached_shipments,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.sync_btn.pack(pady=5)
        self.sync_btn.bind("<Enter>", on_button_enter)
        self.sync_btn.bind("<Leave>", on_button_leave)
        self.undo_btn = ctk.CTkButton(
            frame,
            text=self.translations[self.current_language]["undo"],
            command=self.undo_last_action,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.undo_btn.pack(pady=5)
        self.undo_btn.bind("<Enter>", on_button_enter)
        self.undo_btn.bind("<Leave>", on_button_leave)
        self.theme_btn = ctk.CTkButton(
            frame,
            text=self.translations[self.current_language]["toggle_theme"],
            command=self.toggle_theme,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.theme_btn.pack(pady=5)
        self.theme_btn.bind("<Enter>", on_button_enter)
        self.theme_btn.bind("<Leave>", on_button_leave)
        self.fs_btn = ctk.CTkButton(
            frame,
            text=self.translations[self.current_language]["toggle_fullscreen"],
            command=self.toggle_fullscreen,
            font=self.font_cairo_16,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=TEXT_COLOR
        )
        self.fs_btn.pack(pady=5)
        self.fs_btn.bind("<Enter>", on_button_enter)
        self.fs_btn.bind("<Leave>", on_button_leave)
        # Add Excel Settings Button to Settings Tab
        self.excel_settings_btn = ctk.CTkButton(
            frame,
            text="إعدادات Excel",
            command=self.open_excel_settings,
            font=self.font_cairo_16,
            cursor="hand2"
        )
        self.excel_settings_btn.pack(pady=10)
        # Sound settings frame
        sound_settings_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color=SECONDARY_COLOR)
        sound_settings_frame.pack(pady=10, fill="x")
        sound_title_label = ctk.CTkLabel(
            sound_settings_frame,
            text=self.translations[self.current_language]["sound_settings"],
            font=self.font_cairo_18_bold,
            text_color=TEXT_COLOR
        )
        sound_title_label.pack(pady=5)
        line_check = ctk.CTkCheckBox(
            sound_settings_frame,
            text="إيقاف صوت Line",
            variable=self.silent_line,
            font=self.font_cairo_16,
            text_color=TEXT_COLOR,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            border_color="#666666"
        )
        line_check.pack(pady=5, anchor="w")
        return_check = ctk.CTkCheckBox(
            sound_settings_frame,
            text="إيقاف صوت Return",
            variable=self.silent_return,
            font=self.font_cairo_16,
            text_color=TEXT_COLOR,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            border_color="#666666"
        )
        return_check.pack(pady=5, anchor="w")
        unsimilar_check = ctk.CTkCheckBox(
            sound_settings_frame,
            text="إيقاف صوت غير متطابق",
            variable=self.silent_unsimilar,
            font=self.font_cairo_16,
            text_color=TEXT_COLOR,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            border_color="#666666"
        )
        unsimilar_check.pack(pady=5, anchor="w")

    # دالة فتح نافذة مهام الأوبريشن
    def open_operation_tasks(self):
        try:
            from operation_tasks import OperationTasksWindow
            op_window = OperationTasksWindow(self, self.logged_in_user)
            op_window.grab_set()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح مهام الأوبريشن: {e}")

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

    def load_cached_shipments(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading cache: {e}")
        return []

    def save_shipment_to_cache(self, shipment_data):
        cache = self.load_cached_shipments()
        cache.append(shipment_data)
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f)
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")

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
                activity = EmployeeActivity(
                    employee_id=self.logged_in_user.id,
                    sheet_name=os.path.basename(self.imported_excel_path),
                    shipment_count=import_count
                )
                session.add(activity)
                session.commit()
                messagebox.showinfo(
                    "نجاح",
                    f"تم الاستيراد باستخدام الأعمدة المختارة ({id_col}, {status_col}) بنجاح!"
                )
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

    def clear_shipments(self):
        confirm = messagebox.askyesno("تأكيد", "هل تريد مسح جميع الشحنات من الشاشة؟")
        if confirm:
            self.current_shipments = []
            self.unmatched_shipments = []
            if hasattr(self, 'unmatched_text'):
                self.unmatched_text.delete("1.0", "end")
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()

    def undo_last_action(self):
        if not self.undo_stack:
            messagebox.showinfo("تنبيه", "لا يوجد إجراء للإلغاء!")
            return
        last_action = self.undo_stack.pop()
        shipment_id = last_action["ID"]
        for ship in self.current_shipments:
            if ship["ID"] == shipment_id:
                ship["Checked"] = last_action["previous_checked"]
                ship["inspected_date"] = last_action["previous_inspected_date"]
                break
        session = SessionLocal()
        db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id)\
                         .order_by(Shipment.id.desc()).first()
        if db_shipment:
            db_shipment.checked = last_action["previous_checked"]
            db_shipment.inspected_date = last_action["previous_inspected_date"]
            session.commit()
        session.close()
        self.update_treeview()
        self.update_remaining_text()
        messagebox.showinfo("تنبيه", "تم التراجع عن الإجراء الأخير.")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)

    def toggle_fullscreen(self):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    def change_language(self, selection):
        if selection == "العربية":
            self.current_language = "ar"
        else:
            self.current_language = "en"
        self.update_language()

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

    def open_excel_settings(self):
        # Open the Excel Settings window
        excel_win = ExcelSettingsWindow(self)
        excel_win.grab_set()

    # ------------------------------------------------------------------------------------
    # إضافة زر فتح نافذة مهام الأوبريشن (ميزة الأوبريشن)
    # ------------------------------------------------------------------------------------
    def open_operation_tasks(self):
        try:
            from operation_tasks import OperationTasksWindow
            op_window = OperationTasksWindow(self, self.logged_in_user)
            op_window.grab_set()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح مهام الأوبريشن: {e}")

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

    def clear_shipments(self):
        confirm = messagebox.askyesno("تأكيد", "هل تريد مسح جميع الشحنات من الشاشة؟")
        if confirm:
            self.current_shipments = []
            self.unmatched_shipments = []
            if hasattr(self, 'unmatched_text'):
                self.unmatched_text.delete("1.0", "end")
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()

    def undo_last_action(self):
        if not self.undo_stack:
            messagebox.showinfo("تنبيه", "لا يوجد إجراء للإلغاء!")
            return
        last_action = self.undo_stack.pop()
        shipment_id = last_action["ID"]
        for ship in self.current_shipments:
            if ship["ID"] == shipment_id:
                ship["Checked"] = last_action["previous_checked"]
                ship["inspected_date"] = last_action["previous_inspected_date"]
                break
        session = SessionLocal()
        db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id)\
                         .order_by(Shipment.id.desc()).first()
        if db_shipment:
            db_shipment.checked = last_action["previous_checked"]
            db_shipment.inspected_date = last_action["previous_inspected_date"]
            session.commit()
        session.close()
        self.update_treeview()
        self.update_remaining_text()
        messagebox.showinfo("تنبيه", "تم التراجع عن الإجراء الأخير.")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)

    def toggle_fullscreen(self):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    def change_language(self, selection):
        if selection == "العربية":
            self.current_language = "ar"
        else:
            self.current_language = "en"
        self.update_language()

    def filter_shipments(self, event):
        query = self.search_var.get().strip().lower()
        filtered = [s for s in self.current_shipments if query in s["ID"]]
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in filtered:
            self.tree.insert("", "end", values=(s["ID"], s["Status"], s["Checked"]))

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

    def open_excel_settings(self):
        # Open the Excel Settings window
        excel_win = ExcelSettingsWindow(self)
        excel_win.grab_set()

    def open_operation_tasks(self):
        try:
            from operation_tasks import OperationTasksWindow
            op_window = OperationTasksWindow(self, self.logged_in_user)
            op_window.grab_set()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح مهام الأوبريشن: {e}")

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

    def clear_shipments(self):
        confirm = messagebox.askyesno("تأكيد", "هل تريد مسح جميع الشحنات من الشاشة؟")
        if confirm:
            self.current_shipments = []
            self.unmatched_shipments = []
            if hasattr(self, 'unmatched_text'):
                self.unmatched_text.delete("1.0", "end")
            self.update_treeview()
            self.update_remaining_text()
            self.update_uploaded_count()

    def undo_last_action(self):
        if not self.undo_stack:
            messagebox.showinfo("تنبيه", "لا يوجد إجراء للإلغاء!")
            return
        last_action = self.undo_stack.pop()
        shipment_id = last_action["ID"]
        for ship in self.current_shipments:
            if ship["ID"] == shipment_id:
                ship["Checked"] = last_action["previous_checked"]
                ship["inspected_date"] = last_action["previous_inspected_date"]
                break
        session = SessionLocal()
        db_shipment = session.query(Shipment).filter_by(shipment_id=shipment_id)\
                         .order_by(Shipment.id.desc()).first()
        if db_shipment:
            db_shipment.checked = last_action["previous_checked"]
            db_shipment.inspected_date = last_action["previous_inspected_date"]
            session.commit()
        session.close()
        self.update_treeview()
        self.update_remaining_text()
        messagebox.showinfo("تنبيه", "تم التراجع عن الإجراء الأخير.")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)

    def toggle_fullscreen(self):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

if __name__ == "__main__":
    class DummyUser:
        def __init__(self):
            self.name = "موظف تجريبي"
            self.role = "employee"
            self.id = 999
            self.company_id = 1
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ShipmentCheckerApp(DummyUser())
    app.mainloop()
