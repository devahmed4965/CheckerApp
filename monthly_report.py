import os
import datetime
import calendar
import customtkinter as ctk
from tkinter import messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Windows printing (requires pywin32)
try:
    import win32api
    import win32print
except ImportError:
    win32api = None
    win32print = None

# Import database session and models
from models import SessionLocal, Employee, Shipment

class MonthlyReportWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("التقرير الشهري")
        self.geometry("800x600")

        # Define Cairo fonts
        self.font_cairo_16 = ctk.CTkFont(family="Cairo", size=16)
        self.font_cairo_24_bold = ctk.CTkFont(family="Cairo", size=24, weight="bold")

        # Create a text box to display the report content with Cairo font
        self.report_text = ctk.CTkTextbox(self, wrap="word", width=780, height=500, font=self.font_cairo_16)
        self.report_text.pack(padx=10, pady=10)

        # Load report data: list all employees and their monthly activity
        self.load_report_data()

        # Print button to open print options
        print_btn = ctk.CTkButton(self, text="طباعة التقرير", command=self.print_report, font=self.font_cairo_16)
        print_btn.pack(pady=10)

    def load_report_data(self):
        """
        Generates a monthly report including each employee's name and
        the number of shipments inspected and imported during the current month.
        """
        today = datetime.date.today()
        first_day = today.replace(day=1)
        # Get last day of current month
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        report_content = "تقرير شهري\n"
        report_content += f"الفترة: {first_day} إلى {last_day}\n\n"

        session = SessionLocal()
        employees = session.query(Employee).all()
        for emp in employees:
            inspected_count = session.query(Shipment).filter(
                Shipment.employee_id == emp.id,
                Shipment.checked == True,
                Shipment.inspected_date != None,
                Shipment.inspected_date >= first_day,
                Shipment.inspected_date <= last_day
            ).count()
            imported_count = session.query(Shipment).filter(
                Shipment.employee_id == emp.id,
                Shipment.imported == True,
                Shipment.inspected_date != None,
                Shipment.inspected_date >= first_day,
                Shipment.inspected_date <= last_day
            ).count()
            report_content += f"{emp.name}:\n"
            report_content += f"  مفحوصة: {inspected_count}، مستوردة: {imported_count}\n\n"
        session.close()

        self.report_text.insert("1.0", report_content)

    def print_report(self):
        """
        Generate a PDF from the report text. Then open a new window showing connected printers and
        provide options to print the PDF or save it to a user-selected location.
        """
        pdf_file = os.path.join(os.getcwd(), "monthly_report.pdf")
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, "التقرير الشهري")
        c.setFont("Helvetica", 12)
        textobject = c.beginText(40, height - 100)
        content = self.report_text.get("1.0", "end").strip()
        for line in content.splitlines():
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()

        # If running on Windows with pywin32, open a print options window
        if win32api and win32print:
            options_win = ctk.CTkToplevel(self)
            options_win.title("خيارات الطباعة")
            options_win.geometry("400x200")

            lbl = ctk.CTkLabel(options_win, text="اختر الطابعة:", font=self.font_cairo_16)
            lbl.pack(pady=10)

            # Get list of connected printers
            printers = []
            try:
                # Enumerate local and network printers
                printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                printers = [printer[2] for printer in printer_info]
            except Exception as e:
                printers = []

            printer_combobox = ctk.CTkComboBox(options_win, values=printers, font=self.font_cairo_16, width=300)
            printer_combobox.pack(pady=10)
            if printers:
                printer_combobox.set(printers[0])
            else:
                printer_combobox.set("لا توجد طابعات")

            def do_print():
                selected_printer = printer_combobox.get()
                try:
                    win32api.ShellExecute(
                        0,
                        "print",
                        pdf_file,
                        f'/d:"{selected_printer}"',
                        ".",
                        0
                    )
                    messagebox.showinfo("طباعة", f"تم إرسال الملف للطابعة: {selected_printer}")
                except Exception as e:
                    messagebox.showerror("خطأ في الطباعة", f"حدث خطأ أثناء الطباعة: {e}")

            def save_as_pdf():
                file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
                if file_path:
                    try:
                        import shutil
                        shutil.copy(pdf_file, file_path)
                        messagebox.showinfo("حفظ", f"تم حفظ التقرير كملف PDF في: {file_path}")
                    except Exception as e:
                        messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ الملف: {e}")

            btn_print = ctk.CTkButton(options_win, text="طباعة", command=do_print, font=self.font_cairo_16)
            btn_print.pack(pady=5)
            btn_save = ctk.CTkButton(options_win, text="حفظ كملف PDF", command=save_as_pdf, font=self.font_cairo_16)
            btn_save.pack(pady=5)
        else:
            messagebox.showinfo("تنبيه", f"تم حفظ التقرير كملف PDF:\n{pdf_file}\n\nيرجى استخدام قارئ PDF للطباعة.")
