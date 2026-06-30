import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="crm_db"
    )
    return connection

class CustomersModule:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="white",
                        foreground="#2d3748",
                        rowheight=35,
                        fieldbackground="white",
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading",
                        background="#1e2a3a",
                        foreground="white",
                        font=("Helvetica", 10, "bold"),
                        relief="flat")
        style.map("Treeview",
                 background=[("selected", "#4361ee")],
                 foreground=[("selected", "white")])

    def build_ui(self):
        header = tk.Frame(self.parent, bg="#1e2a3a", pady=18)
        header.pack(fill=tk.X)
        tk.Label(header, text="👥  Customer Management",
                font=("Helvetica", 20, "bold"),
                fg="white", bg="#1e2a3a").pack(side=tk.LEFT, padx=25)
        tk.Button(header, text="＋  Add Customer",
                 font=("Helvetica", 10, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=18, pady=8, cursor="hand2",
                 activebackground="#3451d1",
                 command=self.add_customer).pack(side=tk.RIGHT, padx=25)

        stats_bar = tk.Frame(self.parent, bg="#f4f6f9", pady=12)
        stats_bar.pack(fill=tk.X, padx=20)
        self.stat_labels = {}
        stats = [
            ("total", "👥 Total", "#4361ee"),
            ("active", "✅ Active", "#2ecc71"),
            ("lead", "🔥 Leads", "#f39c12"),
            ("inactive", "❌ Inactive", "#e74c3c"),
        ]
        for key, label, color in stats:
            card = tk.Frame(stats_bar, bg="white", padx=20, pady=8)
            card.pack(side=tk.LEFT, padx=8)
            tk.Label(card, text=label, font=("Helvetica", 9),
                    fg="#6c7a8d", bg="white").pack()
            lbl = tk.Label(card, text="0", font=("Helvetica", 18, "bold"),
                          fg=color, bg="white")
            lbl.pack()
            tk.Frame(card, bg=color, height=3).pack(fill=tk.X, pady=(5,0))
            self.stat_labels[key] = lbl

        search_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        search_frame.pack(fill=tk.X, padx=20)
        search_box = tk.Frame(search_frame, bg="white", pady=6, padx=10)
        search_box.pack(side=tk.LEFT)
        tk.Label(search_box, text="🔍", font=("Helvetica", 12),
                bg="white").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_customers())
        tk.Entry(search_box, textvariable=self.search_var,
                font=("Helvetica", 11), width=25, bd=0,
                fg="#2d3748").pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Filter:",
                font=("Helvetica", 10), bg="#f4f6f9",
                fg="#6c7a8d").pack(side=tk.LEFT, padx=(20,5))
        self.filter_var = tk.StringVar(value="All")
        filter_dd = ttk.Combobox(search_frame, textvariable=self.filter_var,
                                  values=["All", "active", "lead", "inactive"],
                                  font=("Helvetica", 10), width=12,
                                  state="readonly")
        filter_dd.pack(side=tk.LEFT)
        filter_dd.bind("<<ComboboxSelected>>", lambda e: self.load_customers())

        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))

        columns = ("ID", "Name", "Email", "Phone", "Company", "City", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=15)
        widths = [50, 160, 190, 120, 140, 100, 90]
        anchors = [tk.CENTER, tk.W, tk.W, tk.CENTER, tk.W, tk.CENTER, tk.CENTER]
        for col, width, anchor in zip(columns, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("oddrow", background="#f8faff")
        self.tree.tag_configure("evenrow", background="white")
        self.tree.tag_configure("active_tag", foreground="#2ecc71")
        self.tree.tag_configure("lead_tag", foreground="#f39c12")
        self.tree.tag_configure("inactive_tag", foreground="#e74c3c")

        btn_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        buttons = [
            ("✏️  Edit Selected", "#f39c12", "#e67e22", self.edit_customer),
            ("🗑️  Delete Selected", "#e74c3c", "#c0392b", self.delete_customer),
            ("🔄  Refresh", "#2ecc71", "#27ae60", self.load_customers),
        ]
        for text, bg, hover, cmd in buttons:
            btn = tk.Button(btn_frame, text=text,
                           font=("Helvetica", 10, "bold"),
                           fg="white", bg=bg, bd=0, padx=18, pady=7,
                           cursor="hand2", activebackground=hover,
                           activeforeground="white", command=cmd)
            btn.pack(side=tk.LEFT, padx=5)

        self.load_customers()

    def load_customers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            search = self.search_var.get()
            filter_status = self.filter_var.get()
            like = f"%{search}%"

            if filter_status == "All":
                cursor.execute("""SELECT customer_id, full_name, email, phone,
                          company, city, status FROM customers
                          WHERE full_name LIKE %s OR email LIKE %s
                          OR company LIKE %s ORDER BY customer_id DESC""",
                          (like, like, like))
            else:
                cursor.execute("""SELECT customer_id, full_name, email, phone,
                          company, city, status FROM customers
                          WHERE status=%s AND
                          (full_name LIKE %s OR email LIKE %s
                          OR company LIKE %s)
                          ORDER BY customer_id DESC""",
                          (filter_status, like, like, like))

            rows = cursor.fetchall()
            conn.close()

            self.stat_labels["total"].config(text=str(len(rows)))
            self.stat_labels["active"].config(
                text=str(sum(1 for r in rows if r[6]=="active")))
            self.stat_labels["lead"].config(
                text=str(sum(1 for r in rows if r[6]=="lead")))
            self.stat_labels["inactive"].config(
                text=str(sum(1 for r in rows if r[6]=="inactive")))

            for i, row in enumerate(rows):
                tag = "oddrow" if i % 2 == 0 else "evenrow"
                color_tag = f"{row[6]}_tag"
                self.tree.insert("", tk.END, values=row, tags=(tag, color_tag))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_customer(self):
        self.open_form()

    def edit_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a customer first!")
            return
        values = self.tree.item(selected[0])['values']
        self.open_form(values)

    def delete_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a customer first!")
            return
        values = self.tree.item(selected[0])['values']
        if messagebox.askyesno("Delete",
                f"Are you sure you want to delete '{values[1]}'?\n"
                f"All related sales and interactions will also be deleted."):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                # Delete related records first
                cursor.execute(
                    "DELETE FROM notifications WHERE user_id IN "
                    "(SELECT user_id FROM users WHERE user_id=1)")
                cursor.execute(
                    "DELETE FROM interactions WHERE customer_id=%s",
                    (values[0],))
                cursor.execute(
                    "DELETE FROM sales WHERE customer_id=%s",
                    (values[0],))
                cursor.execute(
                    "DELETE FROM feedback WHERE customer_id=%s",
                    (values[0],))
                cursor.execute(
                    "DELETE FROM customers WHERE customer_id=%s",
                    (values[0],))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Customer deleted successfully!")
                self.load_customers()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def open_form(self, data=None):
        form = tk.Toplevel()
        form.title("Add Customer" if not data else "Edit Customer")
        form.configure(bg="white")
        form.grab_set()
        form.resizable(False, False)

        hdr = tk.Frame(form, bg="#1e2a3a", pady=20)
        hdr.pack(fill=tk.X)
        tk.Label(hdr,
                text="👥  Add Customer" if not data else "✏️  Edit Customer",
                font=("Helvetica", 16, "bold"),
                fg="white", bg="#1e2a3a").pack()

        main_frame = tk.Frame(form, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        fields = [
            ("Full Name *", "full_name"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Company", "company"),
            ("City", "city"),
        ]
        entries = {}

        for label, key in fields:
            tk.Label(main_frame, text=label,
                    font=("Helvetica", 10, "bold"),
                    bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(10,0))
            entry_bg = tk.Frame(main_frame, bg="#f0f4ff")
            entry_bg.pack(fill=tk.X)
            entry = tk.Entry(entry_bg, font=("Helvetica", 11),
                           bg="#f0f4ff", bd=0, fg="#2d3748",
                           highlightthickness=0)
            entry.pack(fill=tk.X, padx=10, pady=8)
            tk.Frame(main_frame, bg="#4361ee", height=2).pack(fill=tk.X)
            entries[key] = entry

        tk.Label(main_frame, text="Status",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(12,5))
        status_var = tk.StringVar(value="lead")
        status_frame = tk.Frame(main_frame, bg="white")
        status_frame.pack(anchor=tk.W)
        for val, color, emoji in [("lead", "#f39c12", "🔥"),
                                   ("active", "#2ecc71", "✅"),
                                   ("inactive", "#e74c3c", "❌")]:
            tk.Radiobutton(status_frame,
                          text=f"{emoji} {val.capitalize()}",
                          variable=status_var, value=val,
                          font=("Helvetica", 10, "bold"),
                          bg="white", fg=color,
                          selectcolor="white",
                          activebackground="white",
                          cursor="hand2").pack(side=tk.LEFT, padx=8)

        if data:
            entries["full_name"].insert(0, data[1])
            entries["email"].insert(0, data[2] or "")
            entries["phone"].insert(0, data[3] or "")
            entries["company"].insert(0, data[4] or "")
            entries["city"].insert(0, data[5] or "")
            status_var.set(data[6])

        def save():
            name = entries["full_name"].get().strip()
            if not name:
                messagebox.showwarning("Warning", "Full name is required!")
                return
            try:
                conn = get_connection()
                cursor = conn.cursor()
                if not data:
                    cursor.execute("""INSERT INTO customers
                        (full_name, email, phone, company, city, status)
                        VALUES (%s,%s,%s,%s,%s,%s)""",
                        (name, entries["email"].get(),
                         entries["phone"].get(),
                         entries["company"].get(),
                         entries["city"].get(),
                         status_var.get()))
                else:
                    cursor.execute("""UPDATE customers SET
                        full_name=%s, email=%s, phone=%s,
                        company=%s, city=%s, status=%s
                        WHERE customer_id=%s""",
                        (name, entries["email"].get(),
                         entries["phone"].get(),
                         entries["company"].get(),
                         entries["city"].get(),
                         status_var.get(), data[0]))
                conn.commit()
                conn.close()
                messagebox.showinfo("✅ Success", "Customer saved successfully!")
                form.destroy()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        save_frame = tk.Frame(form, bg="white")
        save_frame.pack(fill=tk.X, padx=30, pady=15)
        tk.Button(save_frame, text="💾  Save Customer",
                 font=("Helvetica", 12, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=20, pady=10, cursor="hand2",
                 activebackground="#3451d1",
                 command=save).pack(fill=tk.X)

        form.update_idletasks()
        form.geometry(f"460x{form.winfo_reqheight()}")