import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
import pymysql  
from PIL import Image  

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

STAFF_NAMES = ["Brenda", "Rahael", "Sammy", "OTHER"]

class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.title("Sammy Worx - Identity Verification")
        self.geometry("400x350")
        self.resizable(False, False)
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self, text="SAMMY WORX", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1F6AA5").pack(pady=(30, 2))
        ctk.CTkLabel(self, text="PRINTS & DESIGN", font=ctk.CTkFont(size=12)).pack(pady=(0, 25))
        self.username_entry = ctk.CTkEntry(self, width=260, placeholder_text="Username")
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, width=260, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)
        self.login_btn = ctk.CTkButton(self, text="Secure Login", width=260, height=35, font=ctk.CTkFont(weight="bold"), command=self.verify_credentials)
        self.login_btn.pack(pady=25)
        self.bind("<Return>", lambda event: self.verify_credentials())

    def verify_credentials(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()
        if user == "admin" and pwd == "worx123":
            self.destroy()
            self.on_login_success(role="admin")
        elif user == "staff" and pwd == "staff256":
            self.destroy()
            self.on_login_success(role="staff")
        else:
            messagebox.showerror("Access Denied", "Invalid Username or Password.")

class SammyWorxApp(ctk.CTk):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role  
        self.current_dash_filter = "today" 
        self.selected_staff_filter = "ALL EMPLOYEES" 
        self.custom_audit_date = datetime.now().strftime("%Y-%m-%d")

        self.title("SAMMY WORX PRINTS & DESIGN - Enterprise Management Portal")
        self.geometry("1250x850")
        self.resizable(True, True)

        try:
            raw_logo = Image.open("logo.png")
            self.sidebar_logo = ctk.CTkImage(light_image=raw_logo, dark_image=raw_logo, size=(100, 100))
        except Exception:
            self.sidebar_logo = None  

        try:
            raw_banner = Image.open("dashboard_banner.png")
            self.dash_banner = ctk.CTkImage(light_image=raw_banner, dark_image=raw_banner, size=(500, 140))
        except Exception:
            self.dash_banner = None  

        # --- FIX: VISIBLE COLUMN HEADERS WITH DARK THEME ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2B2B2B", fieldbackground="#2B2B2B", foreground="white", borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background="#1F6AA5", foreground="white", font=('Arial', 10, 'bold'), borderwidth=1)
        style.map("Treeview.Heading", background=[('active', '#145381')], foreground=[('active', 'white')])
        style.map("Treeview", background=[("selected", "#1F6AA5")])

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        if self.sidebar_logo:
            self.logo_pic_label = ctk.CTkLabel(self.sidebar, text="", image=self.sidebar_logo)
            self.logo_pic_label.pack(pady=(20, 5), padx=20)
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar, text="SAMMY WORX", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1F6AA5")
            self.logo_label.pack(pady=(20, 5))
            
        self.sub_logo = ctk.CTkLabel(self.sidebar, text="PRINTS & DESIGN", font=ctk.CTkFont(size=12))
        self.sub_logo.pack(pady=(0, 20))

        if self.user_role == "admin":
            self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard View", command=self.show_dashboard, fg_color="transparent", text_color="white", anchor="w")
            self.btn_dashboard.pack(fill="x", padx=10, pady=5)

        self.btn_sales_entry = ctk.CTkButton(self.sidebar, text="Sales & Cash Outflow Entry", command=self.show_sales_entry, fg_color="transparent", text_color="white", anchor="w")
        self.btn_sales_entry.pack(fill="x", padx=10, pady=5)

        self.btn_reports = ctk.CTkButton(self.sidebar, text="Reports & Search", command=self.show_reports, fg_color="transparent", text_color="white", anchor="w")
        self.btn_reports.pack(fill="x", padx=10, pady=5)

        if self.user_role == "admin":
            self.btn_messages = ctk.CTkButton(self.sidebar, text="Website Messages (Live)", command=self.show_messages, fg_color="transparent", text_color="white", anchor="w")
            self.btn_messages.pack(fill="x", padx=10, pady=5)

        self.btn_logout = ctk.CTkButton(self.sidebar, text="Exit / Lock App", fg_color="#3A3A3A", hover_color="#C0392B", command=self.quit)
        self.btn_logout.pack(side="bottom", fill="x", padx=10, pady=15)

        self.main_container = ctk.CTkFrame(self, corner_radius=15, fg_color="#1A1A1A")
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        if self.user_role == "admin":
            self.show_dashboard()
        else:
            self.show_sales_entry()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def highlight_button(self, active_button):
        buttons = [self.btn_sales_entry, self.btn_reports]
        if self.user_role == "admin":
            buttons.extend([self.btn_dashboard, self.btn_messages])
        for btn in buttons:
            btn.configure(fg_color="transparent")
        active_button.configure(fg_color="#1F6AA5")

    def fetch_filtered_metrics(self, filter_mode, employee_filter, custom_date_str):
        today = datetime.now().strftime("%Y-%m-%d")
        
        if filter_mode == "custom_audit":
            sql_condition = "WHERE sale_date = %s"
            expense_condition = "WHERE entry_date = %s"
            params = [custom_date_str]
        elif filter_mode == "today":
            sql_condition = "WHERE sale_date = %s"
            expense_condition = "WHERE entry_date = %s"
            params = [today]
        elif filter_mode == "week":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            sql_condition = "WHERE sale_date >= %s"
            expense_condition = "WHERE entry_date >= %s"
            params = [week_ago]
        else:
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            sql_condition = "WHERE sale_date >= %s"
            expense_condition = "WHERE entry_date >= %s"
            params = [month_ago]

        sales_params = list(params)
        expense_params = list(params)

        if employee_filter != "ALL EMPLOYEES":
            sql_condition += " AND sold_by = %s"
            expense_condition += " AND staff_name = %s"
            sales_params.append(employee_filter)
            expense_params.append(employee_filter)

        total_revenue = 0
        total_credit = 0
        total_expenses = 0
        total_count = 0
        staff_breakdown = {}
        detailed_expenses = []

        try:
            conn = pymysql.connect(
                host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                user="21cRDQ1yQsS5317.root",
                password="LZhyUl0yo2bHuMBE",
                database="sammyworx_db",
                port=4000,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            cur = conn.cursor()
            
            # Fetch Cash Revenue
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'PAID'", tuple(sales_params))
            total_revenue = cur.fetchone()[0] or 0
            
            # Fetch Outstanding Credit Debts
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'CREDIT'", tuple(sales_params))
            total_credit = cur.fetchone()[0] or 0

            # Fetch Total Expenses 
            cur.execute(f"SELECT SUM(amount) FROM petty_cash {expense_condition}", tuple(expense_params))
            total_expenses = cur.fetchone()[0] or 0

            # NEW: Fetch Detailed List of who took money and why
            cur.execute(f"SELECT staff_name, amount, reason, entry_time, entry_date FROM petty_cash {expense_condition} ORDER BY id DESC", tuple(expense_params))
            detailed_expenses = cur.fetchall()

            # Fetch Combined Transaction Counts
            cur.execute(f"SELECT COUNT(*) FROM sales {sql_condition}", tuple(sales_params))
            total_count = cur.fetchone()[0] or 0
            
            # Fetch Ledger breakdown by user
            cur.execute(f"SELECT sold_by, SUM(price), COUNT(*) FROM sales {sql_condition} GROUP BY sold_by", tuple(sales_params))
            rows = cur.fetchall()
            for row in rows:
                user = row[0] if row[0] else "N/A"
                staff_breakdown[user] = (row[1] or 0, row[2] or 0)

            conn.close()
        except Exception as e:
            print(f"Metrics Fetch Error: {e}")
            
        return total_revenue, total_credit, total_expenses, total_count, staff_breakdown, detailed_expenses

    # --- VIEW 1: ADMIN DASHBOARD (UPDATED WITH CASH OUTFLOW AUDIT LOGS) ---
    def show_dashboard(self):
        if self.user_role != "admin": return
        self.clear_container()
        self.highlight_button(self.btn_dashboard)
        
        # Create a scrollable outer container so everything fits beautifully on small screens
        scroll_container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        revenue, credit, expenses, entries, staff_data, expense_logs = self.fetch_filtered_metrics(
            self.current_dash_filter, self.selected_staff_filter, self.custom_audit_date
        )

        top_bar = ctk.CTkFrame(scroll_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=30, pady=(15, 5))
        
        lbl = ctk.CTkLabel(top_bar, text="Business Statistics Dashboard", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(side="left")

        filter_frame = ctk.CTkFrame(top_bar, fg_color="#2B2B2B", height=32, corner_radius=8)
        filter_frame.pack(side="right", padx=(10, 0))
        
        modes = [("Today", "today"), ("This Week", "week"), ("This Month", "month")]
        for label, mode_key in modes:
            is_active = (self.current_dash_filter == mode_key)
            btn = ctk.CTkButton(
                filter_frame, text=label, width=85, height=26, corner_radius=6,
                fg_color="#1F6AA5" if is_active else "transparent", text_color="white",
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                command=lambda m=mode_key: self.change_dashboard_filter(m)
            )
            btn.pack(side="left", padx=2, pady=2)

        dropdown_options = ["ALL EMPLOYEES"] + STAFF_NAMES
        self.staff_selector = ctk.CTkComboBox(top_bar, values=dropdown_options, width=150, height=32, command=self.change_staff_filter)
        self.staff_selector.set(self.selected_staff_filter)
        self.staff_selector.pack(side="right", padx=10)

        # HISTORICAL DATE AUDIT TRACKER
        audit_frame = ctk.CTkFrame(scroll_container, fg_color="#222222", corner_radius=10)
        audit_frame.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(audit_frame, text="🔍 Missed a Day? Check Historical Totals:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=15, pady=10)
        self.date_search_entry = ctk.CTkEntry(audit_frame, width=140, placeholder_text="YYYY-MM-DD")
        self.date_search_entry.insert(0, self.custom_audit_date)
        self.date_search_entry.pack(side="left", padx=5, pady=10)
        
        btn_run_audit = ctk.CTkButton(audit_frame, text="View That Specific Day", width=150, fg_color="#27AE60", hover_color="#219653", command=self.execute_historical_date_audit)
        btn_run_audit.pack(side="left", padx=10, pady=10)

        if self.dash_banner and self.current_dash_filter != "custom_audit":
            self.banner_label = ctk.CTkLabel(scroll_container, text="", image=self.dash_banner)
            self.banner_label.pack(anchor="w", padx=30, pady=(5, 5))

        grid_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        grid_frame.pack(fill="x", padx=30, pady=5)

        if self.current_dash_filter == "custom_audit":
            time_label = f"Date: {self.custom_audit_date}"
        else:
            time_label = "Today" if self.current_dash_filter == "today" else ("7 Days" if self.current_dash_filter == "week" else "30 Days")
            
        scope_title = f" [{self.selected_staff_filter}]" if self.selected_staff_filter != "ALL EMPLOYEES" else ""
        net_cash_in_safe = revenue - expenses

        cards = [
            (f"Gross Cash Logged ({time_label}){scope_title}", f"UGX {int(revenue):,}", "#2ECC71"),
            (f"Money Taken Out / Expenses", f"UGX {int(expenses):,}", "#E67E22"),
            (f"EXPECTED CASH IN SAFE", f"UGX {int(net_cash_in_safe):,}", "#F1C40F"),
            (f"Total Credit Owed", f"UGX {int(credit):,}", "#E74C3C")
        ]
        for i, (title, val, color) in enumerate(cards):
            card = ctk.CTkFrame(grid_frame, width=210, height=95, corner_radius=12, fg_color="#2B2B2B")
            card.grid(row=0, column=i, padx=(0, 15), pady=5)
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="#A3A3A3").pack(pady=(12,0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(pady=5)

        # NEW REVENUE SUBSECTION: DETAILED SAFE EXPENSES TRACKER
        ctk.CTkLabel(scroll_container, text="📋 Safe Cash Outflow Logs (Who took money & why)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#E67E22").pack(anchor="w", padx=30, pady=(15, 2))
        expense_log_frame = ctk.CTkFrame(scroll_container, fg_color="#222222", corner_radius=12)
        expense_log_frame.pack(fill="x", padx=30, pady=(0, 10))

        expense_table = ttk.Treeview(expense_log_frame, columns=("Staff", "Amount", "Reason", "Time", "Date"), show="headings", height=4)
        expense_table.heading("Staff", text="Staff Name")
        expense_table.heading("Amount", text="Amount Removed (UGX)")
        expense_table.heading("Reason", text="Stated Reason / Description")
        expense_table.heading("Time", text="Logged Time")
        expense_table.heading("Date", text="Logged Date")
        
        expense_table.column("Staff", width=150, anchor="w")
        expense_table.column("Amount", width=150, anchor="e")
        expense_table.column("Reason", width=350, anchor="w")
        expense_table.column("Time", width=100, anchor="center")
        expense_table.column("Date", width=100, anchor="center")
        expense_table.pack(fill="both", expand=True, padx=12, pady=12)

        if not expense_logs:
            expense_table.insert("", "end", values=("No cash withdrawals recorded", "-", "-", "-", "-"))
        else:
            for log in expense_logs:
                expense_table.insert("", "end", values=(log[0].upper(), f"{int(log[1]):,}", log[2], log[3], log[4]))

        # Employee breakdown summary table
        ctk.CTkLabel(scroll_container, text="Employee Performance Breakdown Summary", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F6AA5").pack(anchor="w", padx=30, pady=(15, 2))
        leaderboard_frame = ctk.CTkFrame(scroll_container, fg_color="#222222", corner_radius=12)
        leaderboard_frame.pack(fill="x", padx=30, pady=(0, 20))

        lead_table = ttk.Treeview(leaderboard_frame, columns=("User", "TotalValue", "Count"), show="headings", height=4)
        lead_table.heading("User", text="Staff Name")
        lead_table.heading("TotalValue", text="Combined Generated Value (Cash + Credit)")
        lead_table.heading("Count", text="Transactions Handled")
        lead_table.column("User", width=200, anchor="w")
        lead_table.column("TotalValue", width=250, anchor="e")
        lead_table.column("Count", width=150, anchor="center")
        lead_table.pack(fill="both", expand=True, padx=12, pady=12)

        if not staff_data:
            lead_table.insert("", "end", values=("No active records match selected filters", "-", "-"))
        else:
            for employee, (emp_rev, emp_count) in staff_data.items():
                lead_table.insert("", "end", values=(employee.upper(), f"{int(emp_rev):,}", f"{emp_count} items"))

    def change_dashboard_filter(self, new_filter):
        self.current_dash_filter = new_filter
        self.show_dashboard()

    def change_staff_filter(self, selected_choice):
        self.selected_staff_filter = selected_choice
        self.show_dashboard()

    def execute_historical_date_audit(self):
        target_date = self.date_search_entry.get().strip()
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
            self.custom_audit_date = target_date
            self.current_dash_filter = "custom_audit"
            self.show_dashboard()
        except ValueError:
            messagebox.showerror("Format Error", "Please input date exactly using format: YYYY-MM-DD\nExample: 2026-06-15")

    # --- VIEW 2: SALES & EXPENSE ENTRY PORTAL ---
    def show_sales_entry(self):
        self.clear_container()
        self.highlight_button(self.btn_sales_entry)

        scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        sales_panel = ctk.CTkFrame(scroll_frame, fg_color="#222222", corner_radius=12)
        sales_panel.pack(fill="x", pady=(0, 20), padx=20)

        ctk.CTkLabel(sales_panel, text="🛒 Record New Sales / Credit Entry", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2ECC71").pack(anchor="w", padx=30, pady=(15, 10))

        ctk.CTkLabel(sales_panel, text="Select Operator Name:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.dropdown_staff = ctk.CTkComboBox(sales_panel, values=STAFF_NAMES, width=400, state="readonly")
        self.dropdown_staff.pack(anchor="w", padx=30, pady=(0, 10))
        self.dropdown_staff.set(STAFF_NAMES[0])

        ctk.CTkLabel(sales_panel, text="Payment Status Option:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.dropdown_status = ctk.CTkComboBox(sales_panel, values=["PAID", "CREDIT"], width=400, state="readonly", command=self.toggle_customer_requirement)
        self.dropdown_status.pack(anchor="w", padx=30, pady=(0, 10))
        self.dropdown_status.set("PAID")

        ctk.CTkLabel(sales_panel, text="Customer Name (Required for Credit entries):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_customer = ctk.CTkEntry(sales_panel, width=400, placeholder_text="Customer Name")
        self.entry_customer.pack(anchor="w", padx=30, pady=(0, 10))
        self.entry_customer.insert(0, "N/A")

        ctk.CTkLabel(sales_panel, text="Item / Service Details Description:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_item = ctk.CTkEntry(sales_panel, width=400, placeholder_text="e.g. Logo Design, Flyer Printing")
        self.entry_item.pack(anchor="w", padx=30, pady=(0, 10))

        ctk.CTkLabel(sales_panel, text="Quantity / Size configurations:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_quantity = ctk.CTkEntry(sales_panel, width=400, placeholder_text="e.g. 50 copies")
        self.entry_quantity.pack(anchor="w", padx=30, pady=(0, 10))

        ctk.CTkLabel(sales_panel, text="Total Price Charged (UGX):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_price = ctk.CTkEntry(sales_panel, width=400, placeholder_text="e.g. 45000")
        self.entry_price.pack(anchor="w", padx=30, pady=(0, 15))

        btn_save_sale = ctk.CTkButton(sales_panel, text="Save Sale Record", fg_color="#2ECC71", hover_color="#27AE60", width=200, height=35, font=ctk.CTkFont(weight="bold"), command=self.save_sale_to_db)
        btn_save_sale.pack(anchor="w", padx=30, pady=(0, 20))

        expense_panel = ctk.CTkFrame(scroll_frame, fg_color="#222222", corner_radius=12)
        expense_panel.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(expense_panel, text="💸 Log Cash Outflow / Taken from Safe Drawer", font=ctk.CTkFont(size=16, weight="bold"), text_color="#E67E22").pack(anchor="w", padx=30, pady=(15, 10))

        ctk.CTkLabel(expense_panel, text="Who is removing the money? (Select Name):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.dropdown_expense_staff = ctk.CTkComboBox(expense_panel, values=STAFF_NAMES, width=400, state="readonly")
        self.dropdown_expense_staff.pack(anchor="w", padx=30, pady=(0, 10))
        self.dropdown_expense_staff.set(STAFF_NAMES[0])

        ctk.CTkLabel(expense_panel, text="Amount of Money Removed (UGX):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_expense_amount = ctk.CTkEntry(expense_panel, width=400, placeholder_text="e.g. 5000")
        self.entry_expense_amount.pack(anchor="w", padx=30, pady=(0, 10))

        ctk.CTkLabel(expense_panel, text="What is the money being used for? (Reason):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_expense_reason = ctk.CTkEntry(expense_panel, width=400, placeholder_text="e.g. Staff Lunch break, Buying fuel")
        self.entry_expense_reason.pack(anchor="w", padx=30, pady=(0, 15))

        btn_save_expense = ctk.CTkButton(expense_panel, text="Log Cash Outflow Record", fg_color="#E67E22", hover_color="#D35400", width=200, height=35, font=ctk.CTkFont(weight="bold"), command=self.save_expense_to_db)
        btn_save_expense.pack(anchor="w", padx=30, pady=(0, 20))

    def toggle_customer_requirement(self, current_selection):
        if current_selection == "CREDIT" and self.entry_customer.get() == "N/A":
            self.entry_customer.delete(0, 'end')
            self.entry_customer.configure(placeholder_text="Enter customer name")
        elif current_selection == "PAID" and self.entry_customer.get() == "":
            self.entry_customer.insert(0, "N/A")

    def save_sale_to_db(self):
        selected_name = self.dropdown_staff.get()
        status_choice = self.dropdown_status.get()
        customer_id = self.entry_customer.get().strip()
        item = self.entry_item.get().strip()
        quantity = self.entry_quantity.get().strip()
        price_text = self.entry_price.get().strip()

        if status_choice == "CREDIT" and (not customer_id or customer_id == "N/A"):
            messagebox.showwarning("Incomplete Data", "Please fill in the Customer's Name for Credit files.")
            return
        if not item or not quantity or not price_text:
            messagebox.showwarning("Incomplete Form", "Please fill regular data fields.")
            return
        try:
            price = float(price_text)
        except ValueError:
            messagebox.showerror("Input Error", "Please input numerical values for prices.")
            return

        try:
            conn = pymysql.connect(
                host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                user="21cRDQ1yQsS5317.root",
                password="LZhyUl0yo2bHuMBE",
                database="sammyworx_db",
                port=4000,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales (item, quantity, price, sale_date, sale_time, sold_by, payment_status, customer_name) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (item, quantity, price, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), selected_name, status_choice, customer_id))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Transaction logged into main cluster.")
            self.entry_item.delete(0, 'end')
            self.entry_quantity.delete(0, 'end')
            self.entry_price.delete(0, 'end')
            self.entry_customer.delete(0, 'end')
            self.entry_customer.insert(0, "N/A")
            self.dropdown_status.set("PAID")
        except Exception as error:
            messagebox.showerror("Network Sync Defect", str(error))

    def save_expense_to_db(self):
        staff_name = self.dropdown_expense_staff.get()
        amount_text = self.entry_expense_amount.get().strip()
        reason = self.entry_expense_reason.get().strip()

        if not amount_text or not reason:
            messagebox.showwarning("Incomplete Fields", "Please enter the amount and reason for removing money.")
            return
        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror("Format Error", "Amount removed must be a clean number value.")
            return

        try:
            conn = pymysql.connect(
                host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                user="21cRDQ1yQsS5317.root",
                password="LZhyUl0yo2bHuMBE",
                database="sammyworx_db",
                port=4000,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO petty_cash (staff_name, amount, reason, entry_date, entry_time) 
                VALUES (%s, %s, %s, %s, %s)""",
                (staff_name, amount, reason, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")))
            conn.commit()
            conn.close()

            messagebox.showinfo("Expense Tracked", f"Successfully recorded UGX {int(amount):,} removed by {staff_name}.")
            self.entry_expense_amount.delete(0, 'end')
            self.entry_expense_reason.delete(0, 'end')
        except Exception as err:
            messagebox.showerror("Database error", f"Could not save expense:\n{str(err)}")

    # --- VIEW 3: REPORTS & SEARCH ---
    def show_reports(self):
        self.clear_container()
        self.highlight_button(self.btn_reports)

        lbl = ctk.CTkLabel(self.main_container, text="Sales History Logs & Audit Files", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(anchor="w", padx=30, pady=(15, 10))

        filter_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        filter_frame.pack(fill="x", padx=30, pady=5)

        self.search_entry = ctk.CTkEntry(filter_frame, width=250, placeholder_text="Search core index...")
        self.search_entry.pack(side="left", padx=(0, 10))

        btn_search = ctk.CTkButton(filter_frame, text="Search / Refresh", width=120, command=self.load_report_data)
        btn_search.pack(side="left", padx=5)

        self.status_view_filter = ctk.CTkComboBox(filter_frame, values=["SHOW ALL RECORDS", "PAID ONLY", "UNPAID CREDIT ONLY"], width=160, command=lambda e: self.load_report_data())
        self.status_view_filter.set("SHOW ALL RECORDS")
        self.status_view_filter.pack(side="left", padx=10)

        if self.user_role == "admin":
            btn_delete = ctk.CTkButton(filter_frame, text="Delete Selected", fg_color="#C0392B", hover_color="#922B21", command=self.delete_selected_sale)
            btn_delete.pack(side="right", padx=5)

        tree_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=30, pady=15)

        self.sales_table = ttk.Treeview(tree_frame, columns=("ID", "Item", "Quantity", "Price", "Status", "Customer", "Date", "SoldBy"), show="headings")
        self.sales_table.heading("ID", text="ID"); self.sales_table.heading("Item", text="Item Name")
        self.sales_table.heading("Quantity", text="Qty Description"); self.sales_table.heading("Price", text="Price (UGX)")
        self.sales_table.heading("Status", text="Status"); self.sales_table.heading("Customer", text="Customer Name")
        self.sales_table.heading("Date", text="Date"); self.sales_table.heading("SoldBy", text="Sold By")
        
        self.sales_table.column("ID", width=35, anchor="center"); self.sales_table.column("Item", width=180)
        self.sales_table.column("Quantity", width=130); self.sales_table.column("Price", width=95, anchor="e")
        self.sales_table.column("Status", width=70, anchor="center"); self.sales_table.column("Customer", width=130)
        self.sales_table.column("Date", width=85, anchor="center"); self.sales_table.column("SoldBy", width=80, anchor="center")
        self.sales_table.pack(fill="both", expand=True)

        self.lbl_summary_bar = ctk.CTkLabel(self.main_container, text="Total Found: 0 Entries", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F6AA5")
        self.lbl_summary_bar.pack(anchor="w", padx=30, pady=(0, 15))
        self.load_report_data()

    def load_report_data(self):
        for row in self.sales_table.get_children():
            self.sales_table.delete(row)
        search_term = self.search_entry.get().strip()
        view_mode = self.status_view_filter.get()
        
        try:
            conn = pymysql.connect(
                host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                user="21cRDQ1yQsS5317.root",
                password="LZhyUl0yo2bHuMBE",
                database="sammyworx_db",
                port=4000,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            cur = conn.cursor()
            base_query = "SELECT id, item, quantity, price, payment_status, customer_name, sale_date, sold_by FROM sales"
            conditions = []
            params = []
            if search_term:
                conditions.append("(item LIKE %s OR sale_date LIKE %s OR sold_by LIKE %s OR customer_name LIKE %s)")
                params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
            if view_mode == "PAID ONLY": conditions.append("payment_status = 'PAID'")
            elif view_mode == "UNPAID CREDIT ONLY": conditions.append("payment_status = 'CREDIT'")
            if conditions: base_query += " WHERE " + " AND ".join(conditions)
            base_query += " ORDER BY id DESC"
            
            cur.execute(base_query, tuple(params))
            rows = cur.fetchall()
            total_amt = 0.0
            for row in rows:
                self.sales_table.insert("", "end", values=(row[0], row[1], row[2], f"{int(row[3]):,}", row[4], row[5], row[6], str(row[7]).upper()))
                total_amt += row[3]
            conn.close()
            self.lbl_summary_bar.configure(text=f"Total Found: {len(rows)} Records | Cumulative Value Evaluation: UGX {int(total_amt):,}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_selected_sale(self):
        if self.user_role != "admin": return
        selected_item = self.sales_table.selection()
        if not selected_item: return
        row_values = self.sales_table.item(selected_item, "values")
        if messagebox.askyesno("Confirm Deletion", f"Permanently remove transaction record ID {row_values[0]}?"):
            try:
                conn = pymysql.connect(
                    host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                    user="21cRDQ1yQsS5317.root",
                    password="LZhyUl0yo2bHuMBE",
                    database="sammyworx_db",
                    port=4000,
                    ssl_verify_cert=False,
                    ssl_verify_identity=False
                )
                cur = conn.cursor()
                cur.execute("DELETE FROM sales WHERE id = %s", (row_values[0],))
                conn.commit()
                conn.close()
                self.load_report_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def show_messages(self):
        if self.user_role != "admin": return
        self.clear_container()
        self.highlight_button(self.btn_messages)
        lbl = ctk.CTkLabel(self.main_container, text="Live Website Client Inquiries Desk", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(anchor="w", padx=30, pady=(15, 10))
        btn_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=5)
        btn_refresh_live = ctk.CTkButton(btn_frame, text="Fetch Live Messages", fg_color="#1F6AA5", font=ctk.CTkFont(weight="bold"), command=self.load_live_website_data)
        btn_refresh_live.pack(side="left", padx=(0, 10))
        msg_tree_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        msg_tree_frame.pack(fill="both", expand=True, padx=30, pady=15)
        
        self.msg_table = ttk.Treeview(msg_tree_frame, columns=("ID", "Name", "Email", "Message", "Date"), show="headings")
        self.msg_table.heading("ID", text="ID"); self.msg_table.heading("Name", text="Client Name")
        self.msg_table.heading("Email", text="Email Address"); self.msg_table.heading("Message", text="Message Content")
        self.msg_table.heading("Date", text="Received Date")
        self.msg_table.pack(fill="both", expand=True)
        self.load_live_website_data()

    def load_live_website_data(self):
        for row in self.msg_table.get_children(): self.msg_table.delete(row)
        try:
            connection = pymysql.connect(
                host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
                user="21cRDQ1yQsS5317.root",
                password="LZhyUl0yo2bHuMBE",
                database="sammyworx_db",
                port=4000,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, email, message, created_at FROM contact_inquiries ORDER BY id DESC")
            rows = cursor.fetchall()
            for row in rows: self.msg_table.insert("", "end", values=(row[0], row[1], row[2], row[3], str(row[4])))
            connection.close()
        except Exception as error: print(error)

def launch_application(role):
    app = SammyWorxApp(user_role=role)
    app.mainloop()

if __name__ == "__main__":
    login_screen = LoginWindow(on_login_success=launch_application)
    login_screen.mainloop()