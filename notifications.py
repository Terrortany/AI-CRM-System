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

class NotificationsModule:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="white",
                        foreground="#2d3748",
                        rowheight=40,
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
        tk.Label(header, text="🔔  Notifications",
                font=("Helvetica", 20, "bold"),
                fg="white", bg="#1e2a3a").pack(side=tk.LEFT, padx=25)
        tk.Button(header, text="＋  Add Notification",
                 font=("Helvetica", 10, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=18, pady=8, cursor="hand2",
                 activebackground="#3451d1",
                 command=self.add_notification).pack(side=tk.RIGHT, padx=25)

        # Stats bar
        stats_bar = tk.Frame(self.parent, bg="#f4f6f9", pady=12)
        stats_bar.pack(fill=tk.X, padx=20)
        self.stat_labels = {}
        stats = [
            ("total", "🔔 Total", "#4361ee"),
            ("unread", "🔴 Unread", "#e74c3c"),
            ("read", "✅ Read", "#2ecc71"),
        ]
        for key, label, color in stats:
            card = tk.Frame(stats_bar, bg="white", padx=25, pady=8)
            card.pack(side=tk.LEFT, padx=8)
            tk.Label(card, text=label, font=("Helvetica", 9),
                    fg="#6c7a8d", bg="white").pack()
            lbl = tk.Label(card, text="0",
                          font=("Helvetica", 18, "bold"),
                          fg=color, bg="white")
            lbl.pack()
            tk.Frame(card, bg=color, height=3).pack(fill=tk.X, pady=(5,0))
            self.stat_labels[key] = lbl

        # Table
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("ID", "Message", "Status", "Date")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=15)
        widths = [50, 450, 100, 180]
        anchors = [tk.CENTER, tk.W, tk.CENTER, tk.CENTER]
        for col, width, anchor in zip(columns, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("unread", background="#fff3cd",
                               foreground="#856404")
        self.tree.tag_configure("read", background="white",
                               foreground="#6c7a8d")

        # Buttons
        btn_frame = tk.Frame(self.parent, bg="#f4f6f9", pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        buttons = [
            ("✅  Mark as Read", "#2ecc71", "#27ae60", self.mark_read),
            ("🗑️  Delete", "#e74c3c", "#c0392b", self.delete_notification),
            ("📬  Mark All Read", "#4361ee", "#3451d1", self.mark_all_read),
            ("🔄  Refresh", "#6c7a8d", "#4a5568", self.load_notifications),
        ]
        for text, bg, hover, cmd in buttons:
            btn = tk.Button(btn_frame, text=text,
                           font=("Helvetica", 10, "bold"),
                           fg="white", bg=bg, bd=0, padx=15, pady=7,
                           cursor="hand2", activebackground=hover,
                           activeforeground="white", command=cmd)
            btn.pack(side=tk.LEFT, padx=5)

        self.auto_generate_notifications()
        self.load_notifications()

    def auto_generate_notifications(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check pending sales
            cursor.execute("""SELECT COUNT(*) FROM sales 
                           WHERE status='pending'""")
            pending = cursor.fetchone()[0]
            if pending > 0:
                cursor.execute("""INSERT INTO notifications (user_id, message)
                    VALUES (%s, %s)""",
                    (self.user['user_id'],
                     f"⏳ You have {pending} pending deal(s). "
                     f"Follow up to close them!"))

            # Check leads
            cursor.execute("""SELECT COUNT(*) FROM customers 
                           WHERE status='lead'""")
            leads = cursor.fetchone()[0]
            if leads > 0:
                cursor.execute("""INSERT INTO notifications (user_id, message)
                    VALUES (%s, %s)""",
                    (self.user['user_id'],
                     f"🔥 {leads} lead(s) need your attention. "
                     f"Convert them into active customers!"))

            # Daily reminder
            cursor.execute("""INSERT INTO notifications (user_id, message)
                VALUES (%s, %s)""",
                (self.user['user_id'],
                 f"📊 Daily Reminder: Review your sales dashboard "
                 f"and update customer records — "
                 f"{datetime.date.today().strftime('%d %B %Y')}"))

            conn.commit()
            conn.close()
        except:
            pass

    def load_notifications(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT notification_id, message,
                          CASE WHEN is_read=1 THEN 'Read' ELSE 'Unread' END,
                          created_at
                          FROM notifications
                          WHERE user_id=%s
                          ORDER BY notification_id DESC""",
                          (self.user['user_id'],))
            rows = cursor.fetchall()
            conn.close()

            total = len(rows)
            unread = sum(1 for r in rows if r[2] == "Unread")
            read = sum(1 for r in rows if r[2] == "Read")

            self.stat_labels["total"].config(text=str(total))
            self.stat_labels["unread"].config(text=str(unread))
            self.stat_labels["read"].config(text=str(read))

            for row in rows:
                tag = "unread" if row[2] == "Unread" else "read"
                self.tree.insert("", tk.END, values=row, tags=(tag,))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mark_read(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a notification!")
            return
        values = self.tree.item(selected[0])['values']
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""UPDATE notifications SET is_read=1
                           WHERE notification_id=%s""", (values[0],))
            conn.commit()
            conn.close()
            self.load_notifications()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mark_all_read(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""UPDATE notifications SET is_read=1
                           WHERE user_id=%s""", (self.user['user_id'],))
            conn.commit()
            conn.close()
            self.load_notifications()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_notification(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a notification!")
            return
        values = self.tree.item(selected[0])['values']
        if messagebox.askyesno("Delete",
                               "Delete this notification?"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""DELETE FROM notifications
                               WHERE notification_id=%s""", (values[0],))
                conn.commit()
                conn.close()
                self.load_notifications()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def add_notification(self):
        form = tk.Toplevel()
        form.title("Add Notification")
        form.configure(bg="white")
        form.grab_set()
        form.resizable(False, False)

        hdr = tk.Frame(form, bg="#1e2a3a", pady=20)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🔔  Add Notification",
                font=("Helvetica", 16, "bold"),
                fg="white", bg="#1e2a3a").pack()

        main_frame = tk.Frame(form, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

        tk.Label(main_frame, text="Message *",
                font=("Helvetica", 10, "bold"),
                bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(8,0))
        msg_bg = tk.Frame(main_frame, bg="#f0f4ff")
        msg_bg.pack(fill=tk.X)
        msg_text = tk.Text(msg_bg, font=("Helvetica", 11),
                          bg="#f0f4ff", bd=0, height=4,
                          fg="#2d3748")
        msg_text.pack(fill=tk.X, padx=10, pady=8)
        tk.Frame(main_frame, bg="#4361ee", height=2).pack(fill=tk.X)

        def save():
            msg = msg_text.get("1.0", tk.END).strip()
            if not msg:
                messagebox.showwarning("Warning", "Please enter a message!")
                return
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO notifications (user_id, message)
                    VALUES (%s, %s)""",
                    (self.user['user_id'], msg))
                conn.commit()
                conn.close()
                messagebox.showinfo("✅ Success", "Notification added!")
                form.destroy()
                self.load_notifications()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        save_frame = tk.Frame(form, bg="white")
        save_frame.pack(fill=tk.X, padx=30, pady=15)
        tk.Button(save_frame, text="💾  Save Notification",
                 font=("Helvetica", 12, "bold"),
                 fg="white", bg="#4361ee", bd=0,
                 padx=20, pady=10, cursor="hand2",
                 activebackground="#3451d1",
                 command=save).pack(fill=tk.X)

        form.update_idletasks()
        form.geometry(f"460x{form.winfo_reqheight()}")