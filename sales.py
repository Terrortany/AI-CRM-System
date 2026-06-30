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

class SalesModule:
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
        # Header
        header = tk.Frame(self.parent, bg="#1e2a3a", pady=18)
        header.pack(fill=tk.X)
        tk.Label(header, text="💰  Sales Management",
                font=("Helvetica", 20, "bold"),
                fg="white", bg="#1e2a3a").pack(side=tk.LEFT, padx=25)
        tk.Button(header, text="＋  Add Sale",
                 font=("Helvetica", 10, "bold"),
                 fg="white", bg="#2ecc71", bd=0,
                 padx=18, pady=8, cursor="hand2",
                 activebackground="#27ae60",
                 command=self.add_sale).pack(side=tk.RIGHT, padx=25)

        # Stats bar
        stats_bar = tk.Frame(self.parent, bg="#f4f6f9", pady=12)
        stats_bar.pack(fill=tk.X, padx=20)
        self.stat_labels = {}
        stats = [
            ("total", "📊 Total Sales", "#4361ee"),
            ("won", "✅ Won", "#2ecc71"),
            ("lost", "❌ Lost", "#e74c3c"),
            ("pending", "⏳ Pending", "#f39c12"),
            ("revenue", "💰 Revenue", "#7209b7"),
        ]
        for key, label, color in stats:
            card = tk.Frame(stats_bar, bg="white", padx=15, pady=8)
            card.pack(side=tk.LEFT, padx=6)
            tk.Label(card, text=label, font=("Helvetica", 9),
                    fg="#6c7a8d", bg="white").pack()
            lbl = tk.Label(card, text="0", font=("Helvetica", 16, "bold"),
                          fg=color, bg="white")
            lbl.pack()
            tk.Frame(card, bg=color, height=3).pack(fill=tk.X, pady=(5,0))
            self.stat_labels[key] = lbl

        # Search & Filter
        search_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        search_frame.pack(fill=tk.X, padx=20)

        search_box = tk.Frame(search_frame, bg="white", pady=6, padx=10)
        search_box.pack(side=tk.LEFT)
        tk.Label(search_box, text="🔍", font=("Helvetica", 12),
                bg="white").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_sales())
        tk.Entry(search_box, textvariable=self.search_var,
                font=("Helvetica", 11), width=25, bd=0,
                fg="#2d3748").pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Filter:",
                font=("Helvetica", 10), bg="#f4f6f9",
                fg="#6c7a8d").pack(side=tk.LEFT, padx=(20,5))
        self.filter_var = tk.StringVar(value="All")
        filter_dd = ttk.Combobox(search_frame, textvariable=self.filter_var,
                                  values=["All", "won", "lost", "pending"],
                                  font=("Helvetica", 10), width=12,
                                  state="readonly")
        filter_dd.pack(side=tk.LEFT)
        filter_dd.bind("<<ComboboxSelected>>", lambda e: self.load_sales())

        # Table
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))

        columns = ("ID", "Customer", "Product", "Amount", "Date", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=15)
        widths = [50, 180, 180, 100, 120, 100]
        anchors = [tk.CENTER, tk.W, tk.W, tk.CENTER, tk.CENTER, tk.CENTER]
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
        self.tree.tag_configure("won_tag", foreground="#2ecc71")
        self.tree.tag_configure("lost_tag", foreground="#e74c3c")
        self.tree.tag_configure("pending_tag", foreground="#f39c12")

        # Buttons
        btn_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        buttons = [
            ("✏️  Edit Selected", "#f39c12", "#e67e22", self.edit_sale),
            ("🗑️  Delete Selected", "#e74c3c", "#c0392b", self.delete_sale),
            ("🔄  Refresh", "#2ecc71", "#27ae60", self.load_sales),
        ]
        for text, bg, hover, cmd in buttons:
            btn = tk.Button(btn_frame, text=text,
                           font=("Helvetica", 10, "bold"),
                           fg="white", bg=bg, bd=0, padx=18, pady=7,
                           cursor="hand2", activebackground=hover,
                           activeforeground="white", command=cmd)
            btn.pack(side=tk.LEFT, padx=5)

        self.load_sales()

    def load_sales(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            search = self.search_var.get()
            filter_status = self.filter_var.get()
            like = f"%{search}%"

            if filter_status == "All":
                cursor.execute("""SELECT s.sale_id, c.full_name,
                          s.product_name, s.amount, s.sale_date, s.status
                          FROM sales s
                          JOIN customers c ON s.customer_id=c.customer_id
                          WHERE c.full_name LIKE %s
                          OR s.product_name LIKE %s
                          ORDER BY s.sale_id DESC""",
                          (like, like))
            else:
                cursor.execute("""SELECT s.sale_id, c.full_name,
                          s.product_name, s.amount, s.sale_date, s.status
                          FROM sales s
                          JOIN customers c ON s.customer_id=c.customer_id
                          WHERE s.status=%s AND
                          (c.full_name LIKE %s OR s.product_name LIKE %s)
                          ORDER BY s.sale_id DESC""",
                          (filter_status, like, like))

            rows = cursor.fetchall()
            conn.close()

            total = len(rows)
            won = sum(1 for r in rows if r[5]=="won")
            lost = sum(1 for r in rows if r[5]=="lost")
            pending = sum(1 for r in rows if r[5]=="pending")
            revenue = sum(float(r[3]) for r in rows if r[5]=="won")

            self.stat_labels["total"].config(text=str(total))
            self.stat_labels["won"].config(text=str(won))
            self.stat_labels["lost"].config(text=str(lost))
            self.stat_labels["pending"].config(text=str(pending))
            self.stat_labels["revenue"].config(text=f"₹{revenue:,.0f}")

            for i, row in enumerate(rows):
                tag = "oddrow" if i % 2 == 0 else "evenrow"
                color_tag = f"{row[5]}_tag"
                display = list(row)
                display[3] = f"₹{float(row[3]):,.0f}"
                self.tree.insert("", tk.END, values=display,
                                tags=(tag, color_tag))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_customers(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT customer_id, full_name FROM customers ORDER BY full_name")
            customers = cursor.fetchall()
            conn.close()
            return customers
        except:
            return []

    def add_sale(self):
        self.open_form()

    def edit_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Pehle ek sale select karo!")
            return
        values = self.tree.item(selected[0])['values']
        self.open_form(values)

    def delete_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Pehle ek sale select karo!")
            return
        values = self.tree.item(selected[0])['values']
        if messagebox.askyesno("Delete", "Is sale ko delete karna chahte ho?"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sales WHERE sale_id=%s", (values[0],))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Sale deleted!")
                self.load_sales()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def open_form(self, data=None):
        form = tk.Toplevel()
        form.title("Add Sale" if not data else "Edit Sale")
        form.configure(bg="white")
        form.grab_set()
        form.resizable(False, False)

        # Header
        hdr = tk.Frame(form, bg="#1e2a3a", pady=20)
        hdr.pack(fill=tk.X)
        tk.Label(hdr,
                text="💰  Add Sale" if not data else "✏️  Edit Sale",
                font=("Helvetica", 16, "bold"),
                fg="white", bg="#1e2a3a").pack()

        main_frame = tk.Frame(form, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # Customer dropdown
        tk.Label(main_frame, text="Customer *",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(8,0))
        customers = self.get_customers()
        customer_names = [f"{c[0]} - {c[1]}" for c in customers]
        self.customer_var = tk.StringVar()
        customer_dd = ttk.Combobox(main_frame, textvariable=self.customer_var,
                                    values=customer_names,
                                    font=("Helvetica", 11), width=35,
                                    state="readonly")
        customer_dd.pack(fill=tk.X, pady=(4,8))

        # Fields
        fields = [
            ("Product Name *", "product"),
            ("Amount (₹) *", "amount"),
            ("Sale Date (YYYY-MM-DD) *", "date"),
        ]
        entries = {}
        for label, key in fields:
            tk.Label(main_frame, text=label,
                    font=("Helvetica", 10, "bold"),
                    bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(8,0))
            entry_bg = tk.Frame(main_frame, bg="#f0f4ff")
            entry_bg.pack(fill=tk.X)
            entry = tk.Entry(entry_bg, font=("Helvetica", 11),
                           bg="#f0f4ff", bd=0, fg="#2d3748")
            entry.pack(fill=tk.X, padx=10, pady=8)
            tk.Frame(main_frame, bg="#4361ee", height=2).pack(fill=tk.X)
            entries[key] = entry

        # Set today's date
        import datetime
        entries["date"].insert(0, datetime.date.today().strftime("%Y-%m-%d"))

        # Status
        tk.Label(main_frame, text="Status",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(12,5))
        status_var = tk.StringVar(value="pending")
        status_frame = tk.Frame(main_frame, bg="white")
        status_frame.pack(anchor=tk.W)
        for val, color, emoji in [("pending", "#f39c12", "⏳"),
                                   ("won", "#2ecc71", "✅"),
                                   ("lost", "#e74c3c", "❌")]:
            tk.Radiobutton(status_frame,
                          text=f"{emoji} {val.capitalize()}",
                          variable=status_var, value=val,
                          font=("Helvetica", 10, "bold"),
                          bg="white", fg=color,
                          selectcolor="white",
                          activebackground="white",
                          cursor="hand2").pack(side=tk.LEFT, padx=8)

        def save():
            if not self.customer_var.get():
                messagebox.showwarning("Warning", "Customer select karo!")
                return
            if not entries["product"].get().strip():
                messagebox.showwarning("Warning", "Product name daalo!")
                return
            if not entries["amount"].get().strip():
                messagebox.showwarning("Warning", "Amount daalo!")
                return
            try:
                customer_id = int(self.customer_var.get().split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO sales
                    (customer_id, user_id, product_name, amount,
                     sale_date, status)
                    VALUES (%s, 1, %s, %s, %s, %s)""",
                    (customer_id,
                     entries["product"].get().strip(),
                     float(entries["amount"].get()),
                     entries["date"].get(),
                     status_var.get()))
                conn.commit()
                conn.close()
                messagebox.showinfo("✅ Success", "Sale saved!")
                form.destroy()
                self.load_sales()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Save button
        save_frame = tk.Frame(form, bg="white")
        save_frame.pack(fill=tk.X, padx=30, pady=15)
        tk.Button(save_frame, text="💾  Save Sale",
                 font=("Helvetica", 12, "bold"),
                 fg="white", bg="#2ecc71", bd=0,
                 padx=20, pady=10, cursor="hand2",
                 activebackground="#27ae60",
                 command=save).pack(fill=tk.X)

        form.update_idletasks()
        form.geometry(f"460x{form.winfo_reqheight()}")