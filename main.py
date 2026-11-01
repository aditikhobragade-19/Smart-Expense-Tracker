import customtkinter as ctk
import sqlite3
import csv
from datetime import date, datetime
from tkinter import messagebox, filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# -------------------- APP SETTINGS --------------------

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = "expenses.db"

CATEGORIES = [
    "Food", "Shopping", "Travel", "Bills",
    "Education", "Health", "Entertainment",
    "Salary", "Business", "Other"
]

BG = "#0B1220"
CARD = "#151F30"
ACCENT = "#7657FF"
GREEN = "#13D6A0"
RED = "#FF647C"
TEXT = "#F4F6FC"
MUTED = "#9AA8BD"


# -------------------- DATABASE --------------------

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# -------------------- MAIN APP --------------------

class SmartExpenseTracker(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Smart Expense Tracker | Aditi Khobragade")
        self.geometry("1180x760")
        self.minsize(950, 650)
        self.configure(fg_color=BG)

        self.conn = connect_db()
        self.selected_id = None
        self.current_page = None
        self.dark_mode = True

        self.show_welcome()

    # -------------------- DATABASE HELPERS --------------------

    def get_budget(self):
        row = self.conn.execute(
            "SELECT setting_value FROM settings WHERE setting_key=?",
            ("monthly_budget",)
        ).fetchone()

        return float(row[0]) if row else 10000.0

    def save_budget(self, amount):
        self.conn.execute("""
            INSERT INTO settings(setting_key, setting_value)
            VALUES(?, ?)
            ON CONFLICT(setting_key)
            DO UPDATE SET setting_value=excluded.setting_value
        """, ("monthly_budget", str(amount)))
        self.conn.commit()

    def get_month_expenses(self):
        month = date.today().strftime("%Y-%m")
        row = self.conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE transaction_type='Expense'
            AND substr(date, 1, 7)=?
        """, (month,)).fetchone()
        return row[0] or 0

    def money(self, amount):
        return f"₹{amount:,.2f}"

    # -------------------- WELCOME SCREEN --------------------

    def show_welcome(self):
        self.current_page = "welcome"

        for widget in self.winfo_children():
            widget.destroy()

        welcome = ctk.CTkFrame(
            self, fg_color=BG, corner_radius=0
        )
        welcome.pack(fill="both", expand=True)

        center = ctk.CTkFrame(
            welcome, fg_color=CARD,
            corner_radius=25, width=650, height=470
        )
        center.place(relx=0.5, rely=0.5, anchor="center")
        center.pack_propagate(False)

        ctk.CTkLabel(
            center, text="💰",
            font=("Arial", 55)
        ).pack(pady=(55, 10))

        ctk.CTkLabel(
            center,
            text="SMART EXPENSE TRACKER",
            font=("Arial", 30, "bold"),
            text_color=TEXT
        ).pack(pady=10)

        ctk.CTkLabel(
            center,
            text="Manage your money. Track your goals.",
            font=("Arial", 16),
            text_color=MUTED
        ).pack(pady=5)

        ctk.CTkLabel(
            center,
            text="A simple and smart way to manage your finances.",
            font=("Arial", 13),
            text_color=MUTED
        ).pack(pady=12)

        ctk.CTkButton(
            center,
            text="GET STARTED  →",
            width=220, height=48,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color="#6040E8",
            font=("Arial", 15, "bold"),
            command=self.show_dashboard
        ).pack(pady=30)

        ctk.CTkLabel(
            center,
            text="Developed by Aditi Khobragade",
            font=("Arial", 12),
            text_color=MUTED
        ).pack(side="bottom", pady=25)

    # -------------------- MAIN DASHBOARD --------------------

    def show_dashboard(self):
        self.current_page = "dashboard"

        for widget in self.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(
            self, fg_color=BG, corner_radius=0
        )
        header.pack(fill="x", padx=25, pady=(18, 8))

        ctk.CTkLabel(
            header,
            text="💰 Smart Expense Tracker",
            font=("Arial", 25, "bold"),
            text_color=TEXT
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="☀ / 🌙 Mode",
            width=110,
            fg_color=CARD,
            hover_color="#26364C",
            command=self.toggle_mode
        ).pack(side="right", padx=5)

        ctk.CTkLabel(
            self,
            text="Take control of your money, one transaction at a time.",
            text_color=MUTED,
            font=("Arial", 13)
        ).pack(anchor="w", padx=28, pady=(0, 12))

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=BG,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#6040E8"
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        self.dashboard_tab = self.tabs.add("Dashboard")
        self.transactions_tab = self.tabs.add("Transactions")
        self.analytics_tab = self.tabs.add("Analytics")
        self.budget_tab = self.tabs.add("Budget")
        self.about_tab = self.tabs.add("About")

        self.build_dashboard_tab()
        self.build_transactions_tab()
        self.build_analytics_tab()
        self.build_budget_tab()
        self.build_about_tab()

        ctk.CTkLabel(
            self,
            text="Smart Expense Tracker  |  Python Project  |  Oasis Infobyte",
            text_color=MUTED,
            font=("Arial", 11)
        ).pack(pady=(0, 10))

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        ctk.set_appearance_mode("Dark" if self.dark_mode else "Light")

    # -------------------- DASHBOARD TAB --------------------

    def build_dashboard_tab(self):
        tab = self.dashboard_tab

        ctk.CTkLabel(
            tab, text="Financial Overview",
            font=("Arial", 23, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 15))

        cards = ctk.CTkFrame(tab, fg_color="transparent")
        cards.pack(fill="x", padx=15)

        self.balance_label = self.create_summary_card(
            cards, "TOTAL BALANCE", GREEN
        )
        self.income_label = self.create_summary_card(
            cards, "TOTAL INCOME", "#39A7FF"
        )
        self.expense_label = self.create_summary_card(
            cards, "TOTAL EXPENSE", RED
        )

        self.today_label = ctk.CTkLabel(
            tab, text="", font=("Arial", 15),
            text_color=MUTED
        )
        self.today_label.pack(anchor="w", padx=22, pady=(25, 8))

        self.month_label = ctk.CTkLabel(
            tab, text="", font=("Arial", 15),
            text_color=MUTED
        )
        self.month_label.pack(anchor="w", padx=22, pady=8)

        self.budget_status_label = ctk.CTkLabel(
            tab, text="", font=("Arial", 15, "bold")
        )
        self.budget_status_label.pack(anchor="w", padx=22, pady=15)

        ctk.CTkButton(
            tab,
            text="＋ Add New Transaction",
            width=220, height=42,
            fg_color=ACCENT,
            command=lambda: self.tabs.set("Transactions")
        ).pack(anchor="w", padx=22, pady=15)

        self.refresh_dashboard()

    def create_summary_card(self, parent, title, color):
        card = ctk.CTkFrame(
            parent, fg_color=CARD,
            corner_radius=16, height=115
        )
        card.pack(
            side="left", fill="both",
            expand=True, padx=7
        )
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, text=title,
            font=("Arial", 12, "bold"),
            text_color=MUTED
        ).pack(pady=(20, 7))

        value = ctk.CTkLabel(
            card, text="₹0.00",
            font=("Arial", 23, "bold"),
            text_color=color
        )
        value.pack()

        return value

    def refresh_dashboard(self):
        row = self.conn.execute("""
            SELECT
            COALESCE(SUM(CASE WHEN transaction_type='Income'
                THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN transaction_type='Expense'
                THEN amount ELSE 0 END), 0)
            FROM transactions
        """).fetchone()

        income, expense = row
        balance = income - expense

        self.income_label.configure(text=self.money(income))
        self.expense_label.configure(text=self.money(expense))
        self.balance_label.configure(text=self.money(balance))

        today = date.today().isoformat()
        today_data = self.conn.execute("""
            SELECT
            COALESCE(SUM(CASE WHEN transaction_type='Income'
                THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN transaction_type='Expense'
                THEN amount ELSE 0 END), 0)
            FROM transactions WHERE date=?
        """, (today,)).fetchone()

        self.today_label.configure(
            text=f"Today's Summary   |   Income: {self.money(today_data[0])}"
                 f"     Expense: {self.money(today_data[1])}"
        )

        month = date.today().strftime("%Y-%m")
        month_data = self.conn.execute("""
            SELECT
            COALESCE(SUM(CASE WHEN transaction_type='Income'
                THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN transaction_type='Expense'
                THEN amount ELSE 0 END), 0)
            FROM transactions WHERE substr(date, 1, 7)=?
        """, (month,)).fetchone()

        self.month_label.configure(
            text=f"This Month   |   Income: {self.money(month_data[0])}"
                 f"     Expense: {self.money(month_data[1])}"
        )

        budget = self.get_budget()
        spent = self.get_month_expenses()

        if spent > budget:
            status = "⚠ Monthly budget exceeded!"
        elif spent >= budget * 0.8:
            status = "⚠ You have used 80% or more of your budget."
        else:
            status = "✓ You are within your monthly budget."

        self.budget_status_label.configure(
            text=f"{status}   ({self.money(spent)} / {self.money(budget)})",
            text_color=RED if spent >= budget * 0.8 else GREEN
        )

    # -------------------- TRANSACTIONS TAB --------------------

    def build_transactions_tab(self):
        tab = self.transactions_tab

        ctk.CTkLabel(
            tab, text="Manage Transactions",
            font=("Arial", 22, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=15)
        form.pack(fill="x", padx=12, pady=8)

        self.title_entry = ctk.CTkEntry(
            form, placeholder_text="Transaction title",
            width=180
        )
        self.title_entry.grid(row=0, column=0, padx=8, pady=12)

        self.amount_entry = ctk.CTkEntry(
            form, placeholder_text="Amount (₹)",
            width=140
        )
        self.amount_entry.grid(row=0, column=1, padx=8, pady=12)

        self.type_menu = ctk.CTkOptionMenu(
            form, values=["Expense", "Income"], width=130
        )
        self.type_menu.grid(row=0, column=2, padx=8, pady=12)

        self.category_menu = ctk.CTkOptionMenu(
            form, values=CATEGORIES, width=145
        )
        self.category_menu.grid(row=0, column=3, padx=8, pady=12)

        self.save_button = ctk.CTkButton(
            form, text="＋ Add",
            fg_color=ACCENT, width=100,
            command=self.add_or_update
        )
        self.save_button.grid(row=0, column=4, padx=8, pady=12)

        ctk.CTkButton(
            form, text="Clear",
            fg_color="#45546A", width=75,
            command=self.clear_form
        ).grid(row=0, column=5, padx=5, pady=12)

        filters = ctk.CTkFrame(tab, fg_color="transparent")
        filters.pack(fill="x", padx=12, pady=8)

        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search title or category...",
            width=260
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind(
            "<KeyRelease>", lambda event: self.refresh_transactions()
        )

        self.filter_menu = ctk.CTkOptionMenu(
            filters,
            values=["All", "Income", "Expense"],
            width=130,
            command=lambda value: self.refresh_transactions()
        )
        self.filter_menu.pack(side="left", padx=5)

        ctk.CTkButton(
            filters, text="Export CSV",
            fg_color=GREEN, text_color="#071A16",
            width=120, command=self.export_csv
        ).pack(side="right", padx=5)

        self.transaction_list = ctk.CTkScrollableFrame(
            tab, fg_color=CARD, corner_radius=15
        )
        self.transaction_list.pack(
            fill="both", expand=True, padx=12, pady=8
        )

        self.refresh_transactions()

    def add_or_update(self):
        title = self.title_entry.get().strip()
        amount_text = self.amount_entry.get().strip()

        if not title or not amount_text:
            messagebox.showwarning(
                "Missing Details", "Please enter title and amount."
            )
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Amount", "Enter a valid amount greater than zero."
            )
            return

        category = self.category_menu.get()
        transaction_type = self.type_menu.get()
        today = date.today().isoformat()

        old_spent = self.get_month_expenses()

        if self.selected_id is None:
            self.conn.execute("""
                INSERT INTO transactions
                (title, amount, category, transaction_type, date)
                VALUES (?, ?, ?, ?, ?)
            """, (title, amount, category, transaction_type, today))
        else:
            self.conn.execute("""
                UPDATE transactions
                SET title=?, amount=?, category=?, transaction_type=?
                WHERE id=?
            """, (
                title, amount, category,
                transaction_type, self.selected_id
            ))

        self.conn.commit()
        self.clear_form()
        self.refresh_transactions()
        self.refresh_dashboard()

        new_spent = self.get_month_expenses()
        budget = self.get_budget()

        if new_spent > budget and new_spent > old_spent:
            messagebox.showwarning(
                "Budget Warning",
                "Your monthly expense has exceeded the budget!"
            )
        elif new_spent >= budget * 0.8 and new_spent > old_spent:
            messagebox.showwarning(
                "Budget Alert",
                "You have used 80% or more of your monthly budget."
            )

        messagebox.showinfo(
            "Success", "Transaction saved successfully!"
        )

    def clear_form(self):
        self.selected_id = None
        self.title_entry.delete(0, "end")
        self.amount_entry.delete(0, "end")
        self.type_menu.set("Expense")
        self.category_menu.set("Food")
        self.save_button.configure(text="＋ Add")

    def edit_transaction(self, transaction):
        transaction_id, title, amount, category, t_type, trans_date = transaction

        self.selected_id = transaction_id

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, title)

        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(amount))

        self.type_menu.set(t_type)
        self.category_menu.set(
            category if category in CATEGORIES else "Other"
        )
        self.save_button.configure(text="✓ Update")

        self.tabs.set("Transactions")

    def delete_transaction(self, transaction_id):
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this transaction?"
        ):
            return

        self.conn.execute(
            "DELETE FROM transactions WHERE id=?",
            (transaction_id,)
        )
        self.conn.commit()

        if self.selected_id == transaction_id:
            self.clear_form()

        self.refresh_transactions()
        self.refresh_dashboard()

    def refresh_transactions(self):
        for widget in self.transaction_list.winfo_children():
            widget.destroy()

        search = self.search_entry.get().strip()
        filter_type = self.filter_menu.get()

        query = """
            SELECT id, title, amount, category,
                   transaction_type, date
            FROM transactions WHERE 1=1
        """
        params = []

        if search:
            query += " AND (title LIKE ? OR category LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        if filter_type != "All":
            query += " AND transaction_type=?"
            params.append(filter_type)

        query += " ORDER BY id DESC"

        records = self.conn.execute(query, params).fetchall()

        if not records:
            ctk.CTkLabel(
                self.transaction_list,
                text="No transactions found.",
                text_color=MUTED,
                font=("Arial", 14)
            ).pack(pady=25)
            return

        for transaction in records:
            tid, title, amount, category, t_type, trans_date = transaction

            row = ctk.CTkFrame(
                self.transaction_list,
                fg_color="#202D40",
                corner_radius=10
            )
            row.pack(fill="x", padx=7, pady=5)

            color = GREEN if t_type == "Income" else RED
            sign = "+" if t_type == "Income" else "-"

            details = (
                f"{title}  |  {category}  |  {trans_date}"
            )

            ctk.CTkLabel(
                row, text=details,
                font=("Arial", 13, "bold"),
                anchor="w"
            ).pack(side="left", padx=12, pady=13, fill="x", expand=True)

            ctk.CTkLabel(
                row, text=f"{sign}{self.money(amount)}",
                text_color=color,
                font=("Arial", 13, "bold"),
                width=130
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                row, text="Edit",
                width=65, height=30,
                fg_color="#3478C8",
                command=lambda item=transaction: self.edit_transaction(item)
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                row, text="Delete",
                width=70, height=30,
                fg_color="#B83D55",
                hover_color="#922C40",
                command=lambda item_id=tid: self.delete_transaction(item_id)
            ).pack(side="left", padx=(4, 10))

    # -------------------- CSV EXPORT --------------------

    def export_csv(self):
        records = self.conn.execute("""
            SELECT id, title, amount, category,
                   transaction_type, date
            FROM transactions ORDER BY date DESC, id DESC
        """).fetchall()

        if not records:
            messagebox.showinfo(
                "No Data", "There are no transactions to export."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="Smart_Expense_Report.csv"
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "ID", "Title", "Amount",
                    "Category", "Type", "Date"
                ])
                writer.writerows(records)

            messagebox.showinfo(
                "Export Successful",
                "Your CSV report has been exported successfully."
            )
        except Exception as error:
            messagebox.showerror("Export Error", str(error))

    # -------------------- ANALYTICS TAB --------------------

    def build_analytics_tab(self):
        tab = self.analytics_tab

        ctk.CTkLabel(
            tab, text="Financial Analytics",
            font=("Arial", 22, "bold")
        ).pack(pady=(35, 10))

        ctk.CTkLabel(
            tab,
            text="Visualize your income and spending patterns.",
            text_color=MUTED,
            font=("Arial", 14)
        ).pack(pady=8)

        ctk.CTkButton(
            tab,
            text="📊 Open Analytics Dashboard",
            width=270, height=48,
            fg_color=ACCENT,
            command=self.show_analytics
        ).pack(pady=25)

        ctk.CTkButton(
            tab,
            text="Export Transactions to CSV",
            width=270, height=42,
            fg_color=GREEN,
            text_color="#071A16",
            command=self.export_csv
        ).pack(pady=8)

    def show_analytics(self):
        window = ctk.CTkToplevel(self)
        window.title("Expense Analytics")
        window.geometry("1050x760")
        window.transient(self)

        ctk.CTkLabel(
            window, text="Your Financial Analytics",
            font=("Arial", 23, "bold")
        ).pack(pady=15)

        figure = plt.Figure(figsize=(10, 6), dpi=100)
        figure.patch.set_facecolor("#151F30")

        ax1 = figure.add_subplot(221)
        ax2 = figure.add_subplot(222)
        ax3 = figure.add_subplot(212)

        for ax in (ax1, ax2, ax3):
            ax.set_facecolor("#202D40")
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.title.set_color("white")

        # Income vs Expense
        totals = self.conn.execute("""
            SELECT transaction_type, COALESCE(SUM(amount), 0)
            FROM transactions GROUP BY transaction_type
        """).fetchall()

        total_map = dict(totals)
        income = total_map.get("Income", 0)
        expense = total_map.get("Expense", 0)

        ax1.bar(
            ["Income", "Expense"],
            [income, expense],
            color=["#13D6A0", "#FF647C"]
        )
        ax1.set_title("Income vs Expense")

        # Category-wise expense
        categories = self.conn.execute("""
            SELECT category, SUM(amount)
            FROM transactions
            WHERE transaction_type='Expense'
            GROUP BY category
        """).fetchall()

        if categories:
            labels = [item[0] for item in categories]
            values = [item[1] for item in categories]
            ax2.pie(
                values, labels=labels,
                autopct="%1.1f%%", textprops={"color": "white"}
            )
            ax2.set_title("Category-wise Expenses")
        else:
            ax2.text(
                0.5, 0.5, "No expense data",
                color="white", ha="center", va="center"
            )
            ax2.set_title("Category-wise Expenses")

        # Monthly expense trend
        monthly = self.conn.execute("""
            SELECT substr(date, 1, 7), SUM(amount)
            FROM transactions
            WHERE transaction_type='Expense'
            GROUP BY substr(date, 1, 7)
            ORDER BY substr(date, 1, 7)
        """).fetchall()

        if monthly:
            months = [item[0] for item in monthly]
            values = [item[1] for item in monthly]
            ax3.plot(
                months, values,
                marker="o", linewidth=2, color="#39A7FF"
            )
            ax3.set_title("Monthly Expense Trend")
            ax3.tick_params(axis="x", rotation=25)
        else:
            ax3.text(
                0.5, 0.5, "No monthly expense data",
                color="white", ha="center", va="center"
            )
            ax3.set_title("Monthly Expense Trend")

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=15, pady=10
        )

        def close_chart():
            plt.close(figure)
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", close_chart)

    # -------------------- BUDGET TAB --------------------

    def build_budget_tab(self):
        tab = self.budget_tab

        ctk.CTkLabel(
            tab, text="Monthly Budget Manager",
            font=("Arial", 22, "bold")
        ).pack(pady=(35, 15))

        ctk.CTkLabel(
            tab,
            text="Set a monthly spending limit and track your expenses.",
            text_color=MUTED,
            font=("Arial", 14)
        ).pack(pady=8)

        self.budget_entry = ctk.CTkEntry(
            tab, width=260,
            placeholder_text="Enter monthly budget (₹)"
        )
        self.budget_entry.pack(pady=15)
        self.budget_entry.insert(0, str(self.get_budget()))

        ctk.CTkButton(
            tab,
            text="Save Monthly Budget",
            width=220,
            fg_color=ACCENT,
            command=self.update_budget
        ).pack(pady=10)

        self.budget_info = ctk.CTkLabel(
            tab, text="",
            font=("Arial", 16, "bold")
        )
        self.budget_info.pack(pady=20)

        self.budget_progress = ctk.CTkProgressBar(
            tab, width=400, progress_color=GREEN
        )
        self.budget_progress.pack(pady=10)

        self.refresh_budget()

    def update_budget(self):
        try:
            amount = float(self.budget_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Budget",
                "Please enter a valid budget greater than zero."
            )
            return

        self.save_budget(amount)
        self.refresh_budget()
        self.refresh_dashboard()

        messagebox.showinfo(
            "Budget Saved", "Monthly budget updated successfully!"
        )

    def refresh_budget(self):
        budget = self.get_budget()
        spent = self.get_month_expenses()
        remaining = budget - spent

        self.budget_info.configure(
            text=f"Budget: {self.money(budget)}\n"
                 f"Spent: {self.money(spent)}\n"
                 f"Remaining: {self.money(remaining)}",
            text_color=RED if remaining < 0 else GREEN
        )

        progress = min(spent / budget, 1.0) if budget > 0 else 0
        self.budget_progress.set(progress)

        self.budget_progress.configure(
            progress_color=RED if spent >= budget * 0.8 else GREEN
        )

    # -------------------- ABOUT TAB --------------------

    def build_about_tab(self):
        tab = self.about_tab

        ctk.CTkLabel(
            tab, text="About This Project",
            font=("Arial", 24, "bold")
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            tab,
            text="SMART EXPENSE TRACKER",
            font=("Arial", 20, "bold"),
            text_color=ACCENT
        ).pack(pady=10)

        description = (
            "A desktop application designed to make personal finance "
            "management simple and organized.\n\n"
            "Features include transaction management, monthly budgets, "
            "financial analytics, search, filters and CSV reports.\n\n"
            "Technologies Used:\n"
            "Python | CustomTkinter | SQLite | Matplotlib\n\n"
            "Developer: Aditi Khobragade\n"
            "Organization: Oasis Infobyte\n"
            "Track: Python Programming"
        )

        ctk.CTkLabel(
            tab,
            text=description,
            font=("Arial", 15),
            text_color=MUTED,
            justify="center"
        ).pack(pady=15)

    # -------------------- CLOSE APP --------------------

    def on_close(self):
        self.conn.close()
        self.destroy()


# -------------------- RUN APPLICATION --------------------

if __name__ == "__main__":
    app = SmartExpenseTracker()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()