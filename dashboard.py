import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="crm_db"
    )
    return connection

class Dashboard:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title("CRM System")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f4f6f9")

        self.main_frame = tk.Frame(self.root, bg="#f4f6f9")
        self.main_frame.pack(fill=BOTH, expand=True)

        self.build_sidebar()

        right = tk.Frame(self.main_frame, bg="#f4f6f9")
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.build_topbar(right)

        self.content = tk.Frame(right, bg="#f4f6f9")
        self.content.pack(fill=BOTH, expand=True)

        self.build_dashboard()

    def build_sidebar(self):
        sidebar = tk.Frame(self.main_frame, bg="#1e2a3a", width=220)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)

        logo = tk.Frame(sidebar, bg="#1a2332", pady=20)
        logo.pack(fill=X)
        tk.Label(logo, text="⭐ CRM Pro", font=("Helvetica", 16, "bold"),
                fg="#ffffff", bg="#1a2332").pack()

        tk.Label(sidebar, text="MAIN", font=("Helvetica", 8),
                fg="#6c7a8d", bg="#1e2a3a").pack(anchor=W, padx=20, pady=(15,5))

        nav_items = [
            ("⊞  Dashboard", self.build_dashboard),
            ("👥  Customers", self.open_customers),
            ("💰  Sales", self.open_sales),
            ("🤝  Interactions", self.open_interactions),
        ]
        for text, cmd in nav_items:
            self.make_nav_btn(sidebar, text, cmd)

        tk.Label(sidebar, text="ANALYTICS", font=("Helvetica", 8),
                fg="#6c7a8d", bg="#1e2a3a").pack(anchor=W, padx=20, pady=(15,5))

        analytics_items = [
            ("🤖  AI Insights", self.open_ai),
            ("🔔  Notifications", self.open_notifications),
        ]
        for text, cmd in analytics_items:
            self.make_nav_btn(sidebar, text, cmd)

        tk.Frame(sidebar, bg="#2d3f55", height=1).pack(fill=X, padx=15, pady=20)
        user_frame = tk.Frame(sidebar, bg="#1e2a3a")
        user_frame.pack(fill=X, padx=15, pady=5)
        tk.Label(user_frame, text="👤", font=("Helvetica", 20),
                bg="#1e2a3a", fg="white").pack(side=LEFT)
        info = tk.Frame(user_frame, bg="#1e2a3a")
        info.pack(side=LEFT, padx=10)
        tk.Label(info, text=self.user['full_name'], font=("Helvetica", 10, "bold"),
                fg="white", bg="#1e2a3a").pack(anchor=W)
        tk.Label(info, text=self.user['role'].upper(), font=("Helvetica", 8),
                fg="#6c7a8d", bg="#1e2a3a").pack(anchor=W)

        tk.Button(sidebar, text="🚪 Logout", font=("Helvetica", 10),
                 fg="#ff6b6b", bg="#1e2a3a", bd=0, pady=10,
                 activebackground="#1a2332", cursor="hand2",
                 command=self.logout).pack(fill=X, padx=20, pady=10)

    def make_nav_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=("Helvetica", 10),
                       fg="#a0aec0", bg="#1e2a3a", bd=0, pady=10,
                       activebackground="#2d3f55", activeforeground="white",
                       cursor="hand2", anchor=W, padx=25,
                       command=cmd)
        btn.pack(fill=X)
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#2d3f55", fg="white"))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#1e2a3a", fg="#a0aec0"))

    def build_topbar(self, parent):
        topbar = tk.Frame(parent, bg="white", pady=12)
        topbar.pack(fill=X)

        hour = datetime.datetime.now().hour
        greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"

        tk.Label(topbar, text=f"{greeting}, {self.user['full_name']} 👋",
                font=("Helvetica", 14, "bold"), fg="#1e2a3a",
                bg="white").pack(side=LEFT, padx=20)

        now = datetime.datetime.now().strftime("%d %B %Y")
        tk.Label(topbar, text=f"📅 {now}", font=("Helvetica", 10),
                fg="#6c7a8d", bg="white").pack(side=RIGHT, padx=20)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def get_stats(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            total_customers = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sales WHERE status='won'")
            total_sales = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM sales WHERE status='won'")
            total_revenue = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sales WHERE status='pending'")
            pending_deals = cursor.fetchone()[0]
            conn.close()
            return total_customers, total_sales, total_revenue, pending_deals
        except:
            return 0, 0, 0, 0

    def build_dashboard(self):
        self.clear_content()
        total_customers, total_sales, total_revenue, pending_deals = self.get_stats()

        canvas = tk.Canvas(self.content, bg="#f4f6f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f4f6f9")
        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        sub = tk.Frame(scroll_frame, bg="#f4f6f9")
        sub.pack(fill=X, padx=20, pady=(15,5))
        tk.Label(sub, text="Contact    Lead    Account",
                font=("Helvetica", 11), fg="#4a5568",
                bg="#f4f6f9").pack(side=LEFT)
        tk.Button(sub, text="+ New Customer", font=("Helvetica", 10, "bold"),
                 fg="white", bg="#4361ee", bd=0, padx=15, pady=5,
                 cursor="hand2").pack(side=RIGHT)

        stats_frame = tk.Frame(scroll_frame, bg="#f4f6f9")
        stats_frame.pack(fill=X, padx=20, pady=10)

        stats = [
            ("Number of Sales", total_sales, "#4361ee"),
            ("Sales Revenue", f"₹{total_revenue:,.0f}", "#7209b7"),
            ("Total Customers", total_customers, "#f72585"),
            ("Pending Deals", pending_deals, "#4cc9f0"),
        ]

        for title, value, color in stats:
            card = tk.Frame(stats_frame, bg="white", padx=20, pady=15)
            card.pack(side=LEFT, expand=True, fill=X, padx=8)
            tk.Label(card, text=title, font=("Helvetica", 9),
                    fg="#6c7a8d", bg="white").pack(anchor=W)
            tk.Label(card, text=str(value), font=("Helvetica", 22, "bold"),
                    fg=color, bg="white").pack(anchor=W)
            tk.Frame(card, bg=color, height=3).pack(fill=X, pady=(10,0))

        charts_row = tk.Frame(scroll_frame, bg="#f4f6f9")
        charts_row.pack(fill=BOTH, expand=True, padx=20, pady=10)

        left_chart = tk.Frame(charts_row, bg="white", padx=10, pady=10)
        left_chart.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,8))
        tk.Label(left_chart, text="Revenue Analytics",
                font=("Helvetica", 12, "bold"), fg="#1e2a3a",
                bg="white").pack(anchor=W, pady=(5,0))
        self.build_bar_chart(left_chart)

        right_chart = tk.Frame(charts_row, bg="white", padx=10, pady=10)
        right_chart.pack(side=LEFT, fill=BOTH, expand=True, padx=(8,0))
        tk.Label(right_chart, text="Sales Analytics",
                font=("Helvetica", 12, "bold"), fg="#1e2a3a",
                bg="white").pack(anchor=W, pady=(5,0))
        self.build_pie_chart(right_chart)

    def build_bar_chart(self, parent):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE_FORMAT(sale_date, '%b') as month,
                COALESCE(SUM(amount),0)
                FROM sales WHERE status='won'
                GROUP BY month ORDER BY MIN(sale_date)
            """)
            data = cursor.fetchall()
            conn.close()

            if not data:
                data = [('Jan',0),('Feb',0),('Mar',0),('Apr',0),
                       ('May',0),('Jun',0),('Jul',0)]

            labels = [r[0] for r in data]
            values = [float(r[1]) for r in data]

            fig = Figure(figsize=(4, 2.5), dpi=90)
            fig.patch.set_facecolor('white')
            ax = fig.add_subplot(111)
            ax.bar(labels, values, color="#4361ee", width=0.5)
            ax.set_facecolor("#f8f9fa")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(labelsize=8)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        except Exception as e:
            tk.Label(parent, text=f"Error: {e}", bg="white").pack()

    def build_pie_chart(self, parent):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM sales GROUP BY status")
            data = cursor.fetchall()
            conn.close()

            if not data:
                data = [('Won', 1), ('Lost', 1), ('Pending', 1)]

            labels = [r[0].capitalize() for r in data]
            values = [r[1] for r in data]
            colors = ["#4361ee", "#4cc9f0", "#f72585"]

            fig = Figure(figsize=(4, 2.5), dpi=90)
            fig.patch.set_facecolor('white')
            ax = fig.add_subplot(111)
            ax.pie(values, labels=labels, colors=colors,
                  autopct='%1.0f%%', startangle=90,
                  wedgeprops=dict(width=0.6))
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        except Exception as e:
            tk.Label(parent, text=f"Error: {e}", bg="white").pack()

    def open_customers(self):
        self.clear_content()
        from modules.customers import CustomersModule
        CustomersModule(self.content)

    def open_sales(self):
        self.clear_content()
        from modules.sales import SalesModule
        SalesModule(self.content)

    def open_interactions(self):
        self.clear_content()
        from modules.interactions import InteractionsModule
        InteractionsModule(self.content)

    def open_ai(self):
        self.clear_content()
        from modules.ai_engine import AIInsightsModule
        AIInsightsModule(self.content)

    def open_notifications(self):
        self.clear_content()
        from modules.notifications import NotificationsModule
        NotificationsModule(self.content, self.user)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            new_root = ttk.Window(themename="flatly")
            from modules.login import LoginWindow
            LoginWindow(new_root)
            new_root.mainloop()