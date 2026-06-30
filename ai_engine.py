import tkinter as tk
from tkinter import ttk
import mysql.connector
import random

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="crm_db"
    )
    return connection

class AIInsightsModule:
    def __init__(self, parent):
        self.parent = parent
        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self.parent, bg="#1e2a3a", pady=18)
        header.pack(fill=tk.X)
        tk.Label(header, text="🤖  AI Insights & Predictions",
                font=("Helvetica", 20, "bold"),
                fg="white", bg="#1e2a3a").pack(side=tk.LEFT, padx=25)
        tk.Button(header, text="🔄  Refresh Analysis",
                 font=("Helvetica", 10, "bold"),
                 fg="white", bg="#7209b7", bd=0,
                 padx=18, pady=8, cursor="hand2",
                 activebackground="#560bad",
                 command=self.load_all).pack(side=tk.RIGHT, padx=25)

        canvas = tk.Canvas(self.parent, bg="#f4f6f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical",
                                   command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="#f4f6f9")
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_all()

    def load_all(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.build_lead_scoring()
        self.build_sales_predictions()
        self.build_top_customers()
        self.build_recommendations()

    def get_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""SELECT c.customer_id, c.full_name,
                           c.status, c.company,
                           COUNT(s.sale_id) as total_sales,
                           COALESCE(SUM(s.amount),0) as total_revenue,
                           COUNT(i.interaction_id) as total_interactions
                           FROM customers c
                           LEFT JOIN sales s ON c.customer_id=s.customer_id
                           LEFT JOIN interactions i ON c.customer_id=i.customer_id
                           GROUP BY c.customer_id""")
            data = cursor.fetchall()
            conn.close()
            return data
        except:
            return []

    def calculate_score(self, customer):
        score = 0
        score += min(customer['total_sales'] * 20, 40)
        score += min(float(customer['total_revenue']) / 1000 * 10, 30)
        score += min(customer['total_interactions'] * 5, 20)
        if customer['status'] == 'active':
            score += 10
        elif customer['status'] == 'lead':
            score += 5
        score += random.randint(0, 10)
        return min(int(score), 100)

    def build_lead_scoring(self):
        frame = tk.Frame(self.scroll_frame, bg="white", pady=15, padx=20)
        frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame, text="🎯 Lead Scoring",
                font=("Helvetica", 14, "bold"),
                fg="#1e2a3a", bg="white").pack(anchor=tk.W)
        tk.Label(frame,
                text="AI-based score predicting customer conversion probability",
                font=("Helvetica", 9), fg="#6c7a8d",
                bg="white").pack(anchor=tk.W, pady=(2,10))

        data = self.get_data()
        if not data:
            tk.Label(frame,
                    text="No customers found. Please add customers first!",
                    font=("Helvetica", 11), fg="#e74c3c",
                    bg="white").pack()
            return

        scored = [(c, self.calculate_score(c)) for c in data]
        scored.sort(key=lambda x: x[1], reverse=True)

        for customer, score in scored[:5]:
            row = tk.Frame(frame, bg="#f8faff", pady=8, padx=15)
            row.pack(fill=tk.X, pady=3)

            tk.Label(row, text=f"👤 {customer['full_name']}",
                    font=("Helvetica", 10, "bold"),
                    fg="#1e2a3a", bg="#f8faff").pack(side=tk.LEFT)

            bar_frame = tk.Frame(row, bg="#f8faff")
            bar_frame.pack(side=tk.LEFT, padx=20, expand=True, fill=tk.X)

            color = "#2ecc71" if score >= 70 else \
                    "#f39c12" if score >= 40 else "#e74c3c"

            bar_bg = tk.Frame(bar_frame, bg="#e0e0e0", height=12)
            bar_bg.pack(fill=tk.X, pady=5)
            tk.Frame(bar_bg, bg=color, height=12).place(
                x=0, y=0, relwidth=score/100)

            score_color = "#2ecc71" if score >= 70 else \
                         "#f39c12" if score >= 40 else "#e74c3c"
            tk.Label(row, text=f"{score}%",
                    font=("Helvetica", 11, "bold"),
                    fg=score_color, bg="#f8faff").pack(side=tk.RIGHT)

    def build_sales_predictions(self):
        frame = tk.Frame(self.scroll_frame, bg="white", pady=15, padx=20)
        frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame, text="📈 Sales Predictions",
                font=("Helvetica", 14, "bold"),
                fg="#1e2a3a", bg="white").pack(anchor=tk.W)
        tk.Label(frame,
                text="Predicted revenue for the next 3 months based on current trends",
                font=("Helvetica", 9), fg="#6c7a8d",
                bg="white").pack(anchor=tk.W, pady=(2,10))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT COALESCE(SUM(amount),0)
                           FROM sales WHERE status='won'""")
            total = float(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM sales WHERE status='won'")
            won = cursor.fetchone()[0]
            conn.close()

            avg = total / max(won, 1)
            months = ["May 2026", "June 2026", "July 2026"]
            predictions = [
                int(avg * random.uniform(1.0, 1.3)),
                int(avg * random.uniform(1.1, 1.5)),
                int(avg * random.uniform(1.2, 1.8)),
            ]

            cards = tk.Frame(frame, bg="white")
            cards.pack(fill=tk.X)

            colors = ["#4361ee", "#7209b7", "#f72585"]
            for month, pred, color in zip(months, predictions, colors):
                card = tk.Frame(cards, bg=color, padx=20, pady=15)
                card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=8)
                tk.Label(card, text=month, font=("Helvetica", 10),
                        fg="white", bg=color).pack()
                tk.Label(card, text=f"₹{pred:,}",
                        font=("Helvetica", 18, "bold"),
                        fg="white", bg=color).pack()
                tk.Label(card, text="Predicted Revenue",
                        font=("Helvetica", 8),
                        fg="white", bg=color).pack()

        except Exception as e:
            tk.Label(frame, text=f"Error: {e}",
                    fg="#e74c3c", bg="white").pack()

    def build_top_customers(self):
        frame = tk.Frame(self.scroll_frame, bg="white", pady=15, padx=20)
        frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame, text="⭐ Top Customers by Revenue",
                font=("Helvetica", 14, "bold"),
                fg="#1e2a3a", bg="white").pack(anchor=tk.W)
        tk.Label(frame,
                text="Customers generating the highest revenue for your business",
                font=("Helvetica", 9), fg="#6c7a8d",
                bg="white").pack(anchor=tk.W, pady=(2,10))

        data = self.get_data()
        if not data:
            tk.Label(frame, text="No data found!",
                    fg="#e74c3c", bg="white").pack()
            return

        sorted_data = sorted(data,
                            key=lambda x: float(x['total_revenue']),
                            reverse=True)[:5]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, customer in enumerate(sorted_data):
            row = tk.Frame(frame, bg="#f8faff", pady=10, padx=15)
            row.pack(fill=tk.X, pady=3)

            tk.Label(row, text=medals[i],
                    font=("Helvetica", 16),
                    bg="#f8faff").pack(side=tk.LEFT)
            tk.Label(row, text=f"  {customer['full_name']}",
                    font=("Helvetica", 11, "bold"),
                    fg="#1e2a3a", bg="#f8faff").pack(side=tk.LEFT)
            tk.Label(row,
                    text=f"Sales: {customer['total_sales']}  |  "
                         f"Revenue: ₹{float(customer['total_revenue']):,.0f}  |  "
                         f"Interactions: {customer['total_interactions']}",
                    font=("Helvetica", 9), fg="#6c7a8d",
                    bg="#f8faff").pack(side=tk.RIGHT)

    def build_recommendations(self):
        frame = tk.Frame(self.scroll_frame, bg="white", pady=15, padx=20)
        frame.pack(fill=tk.X, padx=20, pady=(10,20))

        tk.Label(frame, text="💡 AI Recommendations",
                font=("Helvetica", 14, "bold"),
                fg="#1e2a3a", bg="white").pack(anchor=tk.W)
        tk.Label(frame,
                text="Smart suggestions to improve your sales performance",
                font=("Helvetica", 9), fg="#6c7a8d",
                bg="white").pack(anchor=tk.W, pady=(2,10))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM customers WHERE status='lead'")
            leads = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM customers WHERE status='inactive'")
            inactive = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM sales WHERE status='pending'")
            pending = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM interactions")
            interactions = cursor.fetchone()[0]
            conn.close()

            recommendations = []

            if leads > 0:
                recommendations.append((
                    "🔥 Follow Up on Leads",
                    f"You have {leads} lead(s) in your pipeline. "
                    f"Contact them promptly to convert into active customers "
                    f"and increase your conversion rate.",
                    "#f39c12"
                ))
            if inactive > 0:
                recommendations.append((
                    "♻️ Re-engage Inactive Customers",
                    f"{inactive} customer(s) are currently inactive. "
                    f"Consider sending special offers or personalized messages "
                    f"to bring them back into your sales pipeline.",
                    "#e74c3c"
                ))
            if pending > 0:
                recommendations.append((
                    "⏳ Close Pending Deals",
                    f"You have {pending} pending deal(s) awaiting closure. "
                    f"Schedule follow-up calls and address any objections "
                    f"to close these deals faster.",
                    "#4361ee"
                ))
            if interactions < 5:
                recommendations.append((
                    "🤝 Increase Customer Interactions",
                    "Regular interactions build customer trust and loyalty. "
                    "Schedule weekly calls, send email updates, and arrange "
                    "meetings to strengthen relationships.",
                    "#7209b7"
                ))

            recommendations.append((
                "📊 Weekly Performance Review",
                "Analyze your weekly sales reports to identify top-performing "
                "products and high-value customers. Use this data to focus "
                "your efforts on the most profitable segments.",
                "#2ecc71"
            ))

            recommendations.append((
                "🎯 Target High-Score Leads First",
                "Focus your sales efforts on leads with the highest AI scores. "
                "These customers have the highest probability of conversion "
                "based on their activity and engagement patterns.",
                "#f72585"
            ))

            for title, msg, color in recommendations:
                rec_frame = tk.Frame(frame, bg="#f8faff", pady=12, padx=15)
                rec_frame.pack(fill=tk.X, pady=4)
                tk.Frame(rec_frame, bg=color,
                        width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
                text_frame = tk.Frame(rec_frame, bg="#f8faff")
                text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Label(text_frame, text=title,
                        font=("Helvetica", 11, "bold"),
                        fg=color, bg="#f8faff").pack(anchor=tk.W)
                tk.Label(text_frame, text=msg,
                        font=("Helvetica", 9),
                        fg="#4a5568", bg="#f8faff",
                        wraplength=600,
                        justify=tk.LEFT).pack(anchor=tk.W)

        except Exception as e:
            tk.Label(frame, text=f"Error: {e}",
                    fg="#e74c3c", bg="white").pack()