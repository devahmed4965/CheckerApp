import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import datetime
from models import SessionLocal, OperationTask  # تأكد من تعريف نموذج OperationTask في models.py

class OperationTasksWindow(ctk.CTkToplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.title("مهام الأوبريشن")
        self.geometry("500x400")
        self.logged_in_user = logged_in_user

        # إطار عرض المهام الحالية
        self.tasks_frame = ctk.CTkFrame(self, corner_radius=8)
        self.tasks_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tasks_listbox = tk.Listbox(self.tasks_frame, font=("Cairo", 14))
        self.tasks_listbox.pack(fill="both", expand=True, side="top", pady=5)

        # إطار إدخال مهمة جديدة
        input_frame = ctk.CTkFrame(self, corner_radius=8)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.task_entry = ctk.CTkEntry(input_frame, font=("Cairo", 14), placeholder_text="أدخل نص المهمة هنا...")
        self.task_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        send_btn = ctk.CTkButton(input_frame, text="إرسال", font=("Cairo", 14), command=self.add_task)
        send_btn.pack(side="right", padx=5, pady=5)

        self.load_tasks()

    def load_tasks(self):
        """تحميل المهام من قاعدة البيانات للمستخدم الحالي."""
        session = SessionLocal()
        try:
            tasks = session.query(OperationTask).filter_by(assigned_to=self.logged_in_user.id).all()
            self.tasks_listbox.delete(0, tk.END)
            for task in tasks:
                display_text = f"{task.created_at.strftime('%Y-%m-%d %H:%M')}: {task.title}"
                self.tasks_listbox.insert(tk.END, display_text)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل المهام: {e}")
        finally:
            session.close()

    def add_task(self):
        """إضافة مهمة جديدة بناءً على النص المدخل."""
        task_text = self.task_entry.get().strip()
        if not task_text:
            messagebox.showerror("خطأ", "يرجى إدخال نص المهمة!")
            return
        session = SessionLocal()
        try:
            new_task = OperationTask(
                title=task_text,
                created_by=self.logged_in_user.id,
                assigned_to=self.logged_in_user.id,
                created_at=datetime.datetime.now()
            )
            session.add(new_task)
            session.commit()
            messagebox.showinfo("نجاح", "تم إضافة المهمة بنجاح!")
            self.task_entry.delete(0, tk.END)
            self.load_tasks()
        except Exception as e:
            session.rollback()
            messagebox.showerror("خطأ", f"فشل إضافة المهمة: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    # للتجربة المحلية فقط
    class DummyUser:
        def __init__(self):
            self.id = 1
            self.name = "مستخدم تجريبي"
    root = ctk.CTk()
    op_win = OperationTasksWindow(root, DummyUser())
    op_win.mainloop()
