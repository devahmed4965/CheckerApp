import os
import sys
import customtkinter as ctk
from tkinter import messagebox, filedialog
import pandas as pd
import datetime
from models import SessionLocal, Company

class ExcelSettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("إعدادات Excel")
        self.geometry("500x400")
        self.master = master
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
            company = session.query(Company).filter_by(id=self.master.logged_in_user.company_id).first()
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
