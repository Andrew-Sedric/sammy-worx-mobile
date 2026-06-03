import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
import pymysql  
from PIL import Image  

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Configured list of team member names
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
            messagebox.showerror("Access Denied", "Invalid Username or Password. Please try again.")


class SammyWorxApp(ctk.CTk):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role  
        
        # Dashboard Filter States
        self.current_dash_filter = "today" 
        self.selected_staff_filter = "ALL EMPLOYEES" # Admin dashboard view controller

        self.title("SAMMY WORX PRINTS & DESIGN - Sales Management Application")
        self.geometry("1150x750")
        self.resizable(True, True)

        # =======================================================
        # ASSET LOADING PIPELINE
        # =======================================================
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

        # Table Styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2B2B2B", fieldbackground="#2B2B2B", foreground="white", borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background="#1F6AA5", foreground="white", borderwidth=1)
        style.map("Treeview", background=[("selected", "#1F6AA5")])

        # --- SIDEBAR ---
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

        self.btn_sales_entry = ctk.CTkButton(self.sidebar, text="Sales Entry Portal", command=self.show_sales_entry, fg_color="transparent", text_color="white", anchor="w")
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

    # =======================================================
    # ADVANCED METRIC FILTER WITH AGENT SUB-SORTING
    # =======================================================
    def fetch_filtered_metrics(self, filter_mode, employee_filter):
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Build standard base timeframe filters
        if filter_mode == "today":
            sql_condition = "WHERE sale_date = %s"
            params = [today]
        elif filter_mode == "week":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            sql_condition = "WHERE sale_date >= %s"
            params = [week_ago]
        else:
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            sql_condition = "WHERE sale_date >= %s"
            params = [month_ago]

        # Inject employee verification constraints if looking for someone specific
        if employee_filter != "ALL EMPLOYEES":
            sql_condition += " AND sold_by = %s"
            params.append(employee_filter)

        total_revenue = 0
        total_count = 0
        staff_breakdown = {}

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
            
            # Extract Metrics matching combined Timeframe + Employee selection
            cur.execute(f"SELECT SUM(price), COUNT(*) FROM sales {sql_condition}", tuple(params))
            res = cur.fetchone()
            total_revenue = res[0] or 0
            total_count = res[1] or 0
            
            # Generate the detailed table rows broken down by person
            cur.execute(f"SELECT sold_by, SUM(price), COUNT(*) FROM sales {sql_condition} GROUP BY sold_by", tuple(params))
            rows = cur.fetchall()
            for row in rows:
                user = row[0] if row[0] else "N/A"
                staff_breakdown[user] = (row[1] or 0, row[2] or 0)

            conn.close()
        except Exception as e:
            print(f"Error fetching filtered dashboard values: {e}")
            
        return total_revenue, total_count, staff_breakdown

    # --- VIEW 1: ADMIN DASHBOARD (UPDATED WITH COMBINED FILTERS) ---
    def show_dashboard(self):
        if self.user_role != "admin": return
        self.clear_container()
        self.highlight_button(self.btn_dashboard)
        
        revenue, entries, staff_data = self.fetch_filtered_metrics(self.current_dash_filter, self.selected_staff_filter)

        # Header Control Panel Section
        top_bar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=30, pady=(15, 5))
        
        lbl = ctk.CTkLabel(top_bar, text="Business Statistics Dashboard", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(side="left")

        # Timeframe Control Group
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

        # Dropdown Option Box to isolate individual staff records
        dropdown_options = ["ALL EMPLOYEES"] + STAFF_NAMES
        self.staff_selector = ctk.CTkComboBox(
            top_bar, values=dropdown_options, width=160, height=32,
            command=self.change_staff_filter
        )
        self.staff_selector.set(self.selected_staff_filter)
        self.staff_selector.pack(side="right", padx=10)

        if self.dash_banner:
            self.banner_label = ctk.CTkLabel(self.main_container, text="", image=self.dash_banner)
            self.banner_label.pack(anchor="w", padx=30, pady=(5, 10))

        # Output Summary Performance Displays
        grid_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        grid_frame.pack(fill="x", padx=30, pady=5)

        time_label = "Today" if self.current_dash_filter == "today" else ("7 Days" if self.current_dash_filter == "week" else "30 Days")
        scope_title = f" [{self.selected_staff_filter}]" if self.selected_staff_filter != "ALL EMPLOYEES" else ""
        
        cards = [
            (f"Revenue Total ({time_label}){scope_title}", f"UGX {int(revenue):,}", "#2ECC71"),
            (f"Completed Orders{scope_title}", f"{entries} Receipts Issued", "#3498DB")
        ]
        for i, (title, val, color) in enumerate(cards):
            card = ctk.CTkFrame(grid_frame, width=320, height=90, corner_radius=12, fg_color="#2B2B2B")
            card.grid(row=0, column=i, padx=(0, 20), pady=5)
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13), text_color="#A3A3A3").pack(pady=(12,0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(pady=5)

        # Audit Breakdown Table
        ctk.CTkLabel(self.main_container, text="Employee Ledger Breakdown Summary", font=ctk.CTkFont(size=15, weight="bold"), text_color="#1F6AA5").pack(anchor="w", padx=30, pady=(15, 5))
        
        leaderboard_frame = ctk.CTkFrame(self.main_container, fg_color="#222222", corner_radius=12)
        leaderboard_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        lead_table = ttk.Treeview(leaderboard_frame, columns=("User", "Revenue", "Count"), show="headings", height=5)
        lead_table.heading("User", text="Staff Name")
        lead_table.heading("Revenue", text="Revenue Collected (UGX)")
        lead_table.heading("Count", text="Transactions Closed")
        
        lead_table.column("User", width=200, anchor="w")
        lead_table.column("Revenue", width=250, anchor="e")
        lead_table.column("Count", width=150, anchor="center")
        lead_table.pack(fill="both", expand=True, padx=15, pady=15)

        if not staff_data:
            lead_table.insert("", "end", values=("No active sales history found matching filters", "-", "-"))
        else:
            for employee, (emp_rev, emp_count) in staff_data.items():
                lead_table.insert("", "end", values=(employee.upper(), f"{int(emp_rev):,}", f"{emp_count} items"))

    def change_dashboard_filter(self, new_filter):
        self.current_dash_filter = new_filter
        self.show_dashboard()

    def change_staff_filter(self, selected_choice):
        self.selected_staff_filter = selected_choice
        self.show_dashboard()

    # --- VIEW 2: SALES ENTRY FORM (WITH ROLL DOWN SELECTION DROPDOWN) ---
    def show_sales_entry(self):
        self.clear_container()
        self.highlight_button(self.btn_sales_entry)

        lbl = ctk.CTkLabel(self.main_container, text="Record New Print/Design Sale", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(anchor="w", padx=40, pady=(20, 20))

        form_frame = ctk.CTkFrame(self.main_container, fg_color="#222222", corner_radius=12)
        form_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        # DROPDOWN INTEGRATION: Employee identifier drop down selection
        ctk.CTkLabel(form_frame, text="Sold By / Entered By:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F6AA5").pack(anchor="w", padx=30, pady=(15, 2))
        self.dropdown_staff = ctk.CTkComboBox(form_frame, values=STAFF_NAMES, width=400, state="readonly")
        self.dropdown_staff.pack(anchor="w", padx=30, pady=(0, 15))
        self.dropdown_staff.set(STAFF_NAMES[0]) # Default fallback to Brenda

        ctk.CTkLabel(form_frame, text="Item / Service Name:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_item = ctk.CTkEntry(form_frame, width=400, placeholder_text="Business Cards, Brand Logo, Flyer Printing")
        self.entry_item.pack(anchor="w", padx=30, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Quantity / Description:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_quantity = ctk.CTkEntry(form_frame, width=400, placeholder_text="e.g., 100 copies, A3 Glossy")
        self.entry_quantity.pack(anchor="w", padx=30, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Price (UGX):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=30, pady=(5, 2))
        self.entry_price = ctk.CTkEntry(form_frame, width=400, placeholder_text="e.g., 50000")
        self.entry_price.pack(anchor="w", padx=30, pady=(0, 25))

        btn_save = ctk.CTkButton(form_frame, text="Save Transaction", width=180, height=40, font=ctk.CTkFont(size=15, weight="bold"), command=self.save_sale_to_db)
        btn_save.pack(anchor="w", padx=30, pady=10)

    def save_sale_to_db(self):
        selected_name = self.dropdown_staff.get()
        item = self.entry_item.get().strip()
        quantity = self.entry_quantity.get().strip()
        price_text = self.entry_price.get().strip()

        if not item or not quantity or not price_text:
            messagebox.showwarning("Incomplete Form", "All fields must be filled out.")
            return
        try:
            price = float(price_text)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid price number.")
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
            # Saves the exact selected name from the roll down dropdown menu
            cursor.execute("INSERT INTO sales (item, quantity, price, sale_date, sale_time, sold_by) VALUES (%s, %s, %s, %s, %s, %s)",
                           (item, quantity, price, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), selected_name))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"Transaction saved under operator: {selected_name}")
            self.entry_item.delete(0, 'end')
            self.entry_quantity.delete(0, 'end')
            self.entry_price.delete(0, 'end')
        except Exception as error:
            messagebox.showerror("Cloud Connection Error", f"Failed to save sale onto online server:\n{str(error)}")

    # --- VIEW 3: REPORTS & SEARCH ---
    def show_reports(self):
        self.clear_container()
        self.highlight_button(self.btn_reports)

        lbl = ctk.CTkLabel(self.main_container, text="Sales History & Filter Controls", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(anchor="w", padx=30, pady=(15, 10))

        filter_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        filter_frame.pack(fill="x", padx=30, pady=5)

        self.search_entry = ctk.CTkEntry(filter_frame, width=250, placeholder_text="Search by item name, operator or date...")
        self.search_entry.pack(side="left", padx=(0, 10))

        btn_search = ctk.CTkButton(filter_frame, text="Search / Refresh", width=120, command=self.load_report_data)
        btn_search.pack(side="left", padx=5)

        if self.user_role == "admin":
            btn_delete = ctk.CTkButton(filter_frame, text="Delete Selected Record", fg_color="#C0392B", hover_color="#922B21", command=self.delete_selected_sale)
            btn_delete.pack(side="right", padx=5)

        tree_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=30, pady=15)

        self.sales_table = ttk.Treeview(tree_frame, columns=("ID", "Item", "Quantity", "Price", "Date", "Time", "SoldBy"), show="headings")
        self.sales_table.heading("ID", text="ID"); self.sales_table.heading("Item", text="Item/Service Name")
        self.sales_table.heading("Quantity", text="Quantity/Description"); self.sales_table.heading("Price", text="Price (UGX)")
        self.sales_table.heading("Date", text="Date"); self.sales_table.heading("Time", text="Time"); self.sales_table.heading("SoldBy", text="Sold By")
        
        self.sales_table.column("ID", width=40, anchor="center"); self.sales_table.column("Item", width=220)
        self.sales_table.column("Quantity", width=180); self.sales_table.column("Price", width=110, anchor="e")
        self.sales_table.column("Date", width=90, anchor="center"); self.sales_table.column("Time", width=80, anchor="center")
        self.sales_table.column("SoldBy", width=90, anchor="center")
        self.sales_table.pack(fill="both", expand=True)

        self.lbl_summary_bar = ctk.CTkLabel(self.main_container, text="Total Found: 0 Transactions | Total Amount: UGX 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F6AA5")
        self.lbl_summary_bar.pack(anchor="w", padx=30, pady=(0, 15))
        self.load_report_data()

    def load_report_data(self):
        for row in self.sales_table.get_children():
            self.sales_table.delete(row)
        search_term = self.search_entry.get().strip()
        
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
            if search_term:
                cur.execute("SELECT id, item, quantity, price, sale_date, sale_time, sold_by FROM sales WHERE item LIKE %s OR sale_date LIKE %s OR sold_by LIKE %s ORDER BY id DESC", (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cur.execute("SELECT id, item, quantity, price, sale_date, sale_time, sold_by FROM sales ORDER BY id DESC")
            rows = cur.fetchall()
            total_amt = 0.0
            for row in rows:
                operator = row[6].upper() if row[6] else "N/A"
                self.sales_table.insert("", "end", values=(row[0], row[1], row[2], f"{int(row[3]):,}", row[4], row[5], operator))
                total_amt += row[3]
            conn.close()
            self.lbl_summary_bar.configure(text=f"Total Found: {len(rows)} Transactions | Total Amount: UGX {int(total_amt):,}")
        except Exception as e:
            messagebox.showerror("Cloud Pull Error", f"Could not sync data table from online database:\n{str(e)}")

    def delete_selected_sale(self):
        if self.user_role != "admin": return
        selected_item = self.sales_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Missing", "Please select a row first.")
            return
        row_values = self.sales_table.item(selected_item, "values")
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete record ID {row_values[0]}?"):
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
                messagebox.showerror("Cloud Delete Error", f"Failed to execute remove script on server:\n{str(e)}")

    # --- VIEW 4: LIVE WEBSITE INQUIRIES ---
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
        self.msg_table.heading("ID", text="ID")
        self.msg_table.heading("Name", text="Full Name")
        self.msg_table.heading("Email", text="Email Address")
        self.msg_table.heading("Message", text="Message Details")
        self.msg_table.heading("Date", text="Submitted At")

        self.msg_table.column("ID", width=50, anchor="center")
        self.msg_table.column("Name", width=160)
        self.msg_table.column("Email", width=200)
        self.msg_table.column("Message", width=450)
        self.msg_table.column("Date", width=140, anchor="center")
        self.msg_table.pack(fill="both", expand=True)

        self.load_live_website_data()

    def load_live_website_data(self):
        for row in self.msg_table.get_children():
            self.msg_table.delete(row)
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
            for row in rows:
                date_str = str(row[4]) if row[4] else "N/A"
                self.msg_table.insert("", "end", values=(row[0], row[1], row[2], row[3], date_str))
            connection.close()
        except Exception as error:
            messagebox.showerror("Live Database Sync Error", f"Could not pull records directly:\n{str(error)}")


def launch_application(role):
    app = SammyWorxApp(user_role=role)
    app.mainloop()


if __name__ == "__main__":
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item VARCHAR(255) NOT NULL,
                quantity VARCHAR(255) NOT NULL,
                price DOUBLE NOT NULL,
                sale_date VARCHAR(50) NOT NULL,
                sale_time VARCHAR(50) NOT NULL
            )
        """)
        
        try:
            cursor.execute("ALTER TABLE sales ADD COLUMN sold_by VARCHAR(50) DEFAULT 'N/A'")
            connection.commit()
        except Exception:
            pass
            
        connection.close()
    except Exception as e:
        print(f"Cloud initialization layout check failed: {e}")

    login_screen = LoginWindow(on_login_success=launch_application)
    login_screen.mainloop()