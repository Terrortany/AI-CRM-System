import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
import datetime

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="crm_db"
    )
    return connection

class InteractionsModule:
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
        tk.Label(header, text="🤝  Interactions",
                font=("Helvetica", 20, "bold"),
                fg="white", bg="#1e2a3a").pack(side=tk.LEFT, padx=25)
        tk.Button(header, text="＋  Add Interaction",
                 font=("Helvetica", 10, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=18, pady=8, cursor="hand2",
                 activebackground="#3451d1",
                 command=self.add_interaction).pack(side=tk.RIGHT, padx=25)

        # Stats bar
        stats_bar = tk.Frame(self.parent, bg="#f4f6f9", pady=12)
        stats_bar.pack(fill=tk.X, padx=20)
        self.stat_labels = {}
        stats = [
            ("total", "📊 Total", "#4361ee"),
            ("call", "📞 Calls", "#2ecc71"),
            ("email", "📧 Emails", "#f39c12"),
            ("meeting", "🤝 Meetings", "#7209b7"),
            ("follow_up", "🔔 Follow Ups", "#e74c3c"),
        ]
        for key, label, color in stats:
            card = tk.Frame(stats_bar, bg="white", padx=15, pady=8)
            card.pack(side=tk.LEFT, padx=6)
            tk.Label(card, text=label, font=("Helvetica", 9),
                    fg="#6c7a8d", bg="white").pack()
            lbl = tk.Label(card, text="0",
                          font=("Helvetica", 16, "bold"),
                          fg=color, bg="white")
            lbl.pack()
            tk.Frame(card, bg=color, height=3).pack(fill=tk.X, pady=(5,0))
            self.stat_labels[key] = lbl

        # Search
        search_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        search_frame.pack(fill=tk.X, padx=20)
        search_box = tk.Frame(search_frame, bg="white", pady=6, padx=10)
        search_box.pack(side=tk.LEFT)
        tk.Label(search_box, text="🔍", font=("Helvetica", 12),
                bg="white").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_interactions())
        tk.Entry(search_box, textvariable=self.search_var,
                font=("Helvetica", 11), width=25, bd=0,
                fg="#2d3748").pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Filter:",
                font=("Helvetica", 10), bg="#f4f6f9",
                fg="#6c7a8d").pack(side=tk.LEFT, padx=(20,5))
        self.filter_var = tk.StringVar(value="All")
        filter_dd = ttk.Combobox(search_frame,
                                  textvariable=self.filter_var,
                                  values=["All", "call", "email",
                                         "meeting", "follow_up"],
                                  font=("Helvetica", 10), width=12,
                                  state="readonly")
        filter_dd.pack(side=tk.LEFT)
        filter_dd.bind("<<ComboboxSelected>>",
                       lambda e: self.load_interactions())

        # Table
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))

        columns = ("ID", "Customer", "Type", "Notes", "Date")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=15)
        widths = [50, 180, 100, 300, 150]
        anchors = [tk.CENTER, tk.W, tk.CENTER, tk.W, tk.CENTER]
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
        self.tree.tag_configure("call_tag", foreground="#2ecc71")
        self.tree.tag_configure("email_tag", foreground="#f39c12")
        self.tree.tag_configure("meeting_tag", foreground="#7209b7")
        self.tree.tag_configure("follow_up_tag", foreground="#e74c3c")

        # Buttons
        btn_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        buttons = [
            ("🗑️  Delete Selected", "#e74c3c", "#c0392b", self.delete_interaction),
            ("🔄  Refresh", "#2ecc71", "#27ae60", self.load_interactions),
        ]
        for text, bg, hover, cmd in buttons:
            btn = tk.Button(btn_frame, text=text,
                           font=("Helvetica", 10, "bold"),
                           fg="white", bg=bg, bd=0, padx=18, pady=7,
                           cursor="hand2", activebackground=hover,
                           activeforeground="white", command=cmd)
            btn.pack(side=tk.LEFT, padx=5)

        self.load_interactions()

    def load_interactions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            search = self.search_var.get()
            filter_type = self.filter_var.get()
            like = f"%{search}%"

            if filter_type == "All":
                cursor.execute("""SELECT i.interaction_id, c.full_name,
                          i.type, i.notes, i.interaction_date
                          FROM interactions i
                          JOIN customers c ON i.customer_id=c.customer_id
                          WHERE c.full_name LIKE %s OR i.notes LIKE %s
                          ORDER BY i.interaction_id DESC""",
                          (like, like))
            else:
                cursor.execute("""SELECT i.interaction_id, c.full_name,
                          i.type, i.notes, i.interaction_date
                          FROM interactions i
                          JOIN customers c ON i.customer_id=c.customer_id
                          WHERE i.type=%s AND
                          (c.full_name LIKE %s OR i.notes LIKE %s)
                          ORDER BY i.interaction_id DESC""",
                          (filter_type, like, like))

            rows = cursor.fetchall()
            conn.close()

            self.stat_labels["total"].config(text=str(len(rows)))
            self.stat_labels["call"].config(
                text=str(sum(1 for r in rows if r[2]=="call")))
            self.stat_labels["email"].config(
                text=str(sum(1 for r in rows if r[2]=="email")))
            self.stat_labels["meeting"].config(
                text=str(sum(1 for r in rows if r[2]=="meeting")))
            self.stat_labels["follow_up"].config(
                text=str(sum(1 for r in rows if r[2]=="follow_up")))

            for i, row in enumerate(rows):
                tag = "oddrow" if i % 2 == 0 else "evenrow"
                color_tag = f"{row[2]}_tag"
                self.tree.insert("", tk.END, values=row,
                                tags=(tag, color_tag))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_customers(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT customer_id, full_name 
                           FROM customers ORDER BY full_name""")
            customers = cursor.fetchall()
            conn.close()
            return customers
        except:
            return []

    def add_interaction(self):
        self.open_form()

    def delete_interaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Pehle ek interaction select karo!")
            return
        values = self.tree.item(selected[0])['values']
        if messagebox.askyesno("Delete", "Is interaction ko delete karna chahte ho?"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""DELETE FROM interactions 
                               WHERE interaction_id=%s""", (values[0],))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Interaction deleted!")
                self.load_interactions()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def open_form(self, data=None):
        form = tk.Toplevel()
        form.title("Add Interaction")
        form.configure(bg="white")
        form.grab_set()
        form.resizable(False, False)

        # Header
        hdr = tk.Frame(form, bg="#1e2a3a", pady=20)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🤝  Add Interaction",
                font=("Helvetica", 16, "bold"),
                fg="white", bg="#1e2a3a").pack()

        main_frame = tk.Frame(form, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # Customer
        tk.Label(main_frame, text="Customer *",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(8,0))
        customers = self.get_customers()
        customer_names = [f"{c[0]} - {c[1]}" for c in customers]
        self.customer_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.customer_var,
                    values=customer_names,
                    font=("Helvetica", 11), width=35,
                    state="readonly").pack(fill=tk.X, pady=(4,8))

        # Type
        tk.Label(main_frame, text="Interaction Type *",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(8,5))
        type_var = tk.StringVar(value="call")
        type_frame = tk.Frame(main_frame, bg="white")
        type_frame.pack(anchor=tk.W)
        for val, color, emoji in [("call", "#2ecc71", "📞"),
                                   ("email", "#f39c12", "📧"),
                                   ("meeting", "#7209b7", "🤝"),
                                   ("follow_up", "#e74c3c", "🔔")]:
            tk.Radiobutton(type_frame,
                          text=f"{emoji} {val.replace('_',' ').title()}",
                          variable=type_var, value=val,
                          font=("Helvetica", 9, "bold"),
                          bg="white", fg=color,
                          selectcolor="white",
                          cursor="hand2").pack(side=tk.LEFT, padx=5)

        # Notes
        tk.Label(main_frame, text="Notes",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(12,0))
        notes_bg = tk.Frame(main_frame, bg="#f0f4ff")
        notes_bg.pack(fill=tk.X)
        notes_text = tk.Text(notes_bg, font=("Helvetica", 11),
                            bg="#f0f4ff", bd=0, height=4,
                            fg="#2d3748")
        notes_text.pack(fill=tk.X, padx=10, pady=8)
        tk.Frame(main_frame, bg="#4361ee", height=2).pack(fill=tk.X)

        def save():
            if not self.customer_var.get():
                messagebox.showwarning("Warning", "Customer select karo!")
                return
            try:
                customer_id = int(self.customer_var.get().split(" - ")[0])
                notes = notes_text.get("1.0", tk.END).strip()
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO interactions
                    (customer_id, user_id, type, notes)
                    VALUES (%s, 1, %s, %s)""",
                    (customer_id, type_var.get(), notes))
                conn.commit()
                conn.close()
                messagebox.showinfo("✅ Success", "Interaction saved!")
                form.destroy()
                self.load_interactions()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        save_frame = tk.Frame(form, bg="white")
        save_frame.pack(fill=tk.X, padx=30, pady=15)
        tk.Button(save_frame, text="💾  Save Interaction",
                 font=("Helvetica", 12, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=20, pady=10, cursor="hand2",
                 activebackground="#3451d1",
                 command=save).pack(fill=tk.X)

        form.update_idletasks()
        form.geometry(f"480x{form.winfo_reqheight()}")