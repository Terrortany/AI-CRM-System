import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import tkinter.messagebox as mb
import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="crm_db"
    )
    return connection

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("CRM System - Login")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True, fill=BOTH)

        ttk.Label(frame, text="CRM System", font=("Helvetica", 24, "bold"),
                  bootstyle="primary").pack(pady=(20, 5))
        ttk.Label(frame, text="Sales & Customer Management",
                  font=("Helvetica", 10)).pack(pady=(0, 30))

        ttk.Label(frame, text="Email", font=("Helvetica", 11)).pack(anchor=W)
        self.email_entry = ttk.Entry(frame, width=35, font=("Helvetica", 11))
        self.email_entry.pack(pady=(2, 15), ipady=5)

        ttk.Label(frame, text="Password", font=("Helvetica", 11)).pack(anchor=W)
        self.password_entry = ttk.Entry(frame, width=35, font=("Helvetica", 11), show="*")
        self.password_entry.pack(pady=(2, 25), ipady=5)

        ttk.Button(frame, text="Login", bootstyle="primary",
                   width=30, command=self.login).pack(pady=5)

        ttk.Label(frame, text="Default: admin@crm.com / admin123",
                  font=("Helvetica", 9), bootstyle="secondary").pack(pady=(20, 0))

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Warning", "Please enter email and password!")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                           (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                self.open_dashboard(user)
            else:
                messagebox.showerror("Error", "Invalid email or password!")

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def open_dashboard(self, user):
        try:
            self.root.withdraw()
            from modules.dashboard import Dashboard
            new_root = ttk.Window(themename="flatly")
            Dashboard(new_root, user)
            new_root.mainloop()
            self.root.destroy()
        except Exception as e:
            self.root.deiconify()
            mb.showerror("Dashboard Error", str(e))