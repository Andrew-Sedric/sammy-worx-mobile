import streamlit as st
import pymysql
from datetime import datetime, timedelta, timezone

# Configure page layout
st.set_page_config(page_title="Sammy Worx Admin", page_icon="📊", layout="centered")

# List of team members matching the desktop application exactly
STAFF_NAMES = ["Brenda", "Rahael", "Sammy", "OTHER"]

# Database connection helper
def get_db_connection():
    return pymysql.connect(
        host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
        user="21cRDQ1yQsS5317.root",
        password="LZhyUl0yo2bHuMBE",
        database="sammyworx_db",
        port=4000,
        ssl_verify_cert=False,
        ssl_verify_identity=False
    )

# DATABASE INITIALIZATION
def initialize_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS safe_outflows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reason VARCHAR(255) NOT NULL,
                amount DOUBLE NOT NULL,
                date_logged VARCHAR(50) NOT NULL,
                time_logged VARCHAR(50) NOT NULL,
                logged_by VARCHAR(50) DEFAULT 'N/A'
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to initialize database tables: {e}")

initialize_database()

# Fetch absolutely ALL sales for a specific date
def fetch_all_sales_for_date(target_date):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT item, price, sold_by, sale_time, payment_status, customer_name 
            FROM sales WHERE sale_date = %s ORDER BY id ASC
        """, (target_date,))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def fetch_mobile_metrics(filter_mode, employee_filter):
    uganda_tz = timezone(timedelta(hours=3))
    today_dt = datetime.now(uganda_tz)
    today = today_dt.strftime("%Y-%m-%d")
    
    if filter_mode == "Today":
        sql_condition = "WHERE sale_date = %s"
        outflow_condition = "WHERE date_logged = %s"
        params = [today]
        outflow_params = [today]
    elif filter_mode == "This Week":
        week_ago = (today_dt - timedelta(days=7)).strftime("%Y-%m-%d")
        sql_condition = "WHERE sale_date >= %s"
        outflow_condition = "WHERE date_logged >= %s"
        params = [week_ago]
        outflow_params = [week_ago]
    else:
        month_ago = (today_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        sql_condition = "WHERE sale_date >= %s"
        outflow_condition = "WHERE date_logged >= %s"
        params = [month_ago]
        outflow_params = [month_ago]

    if employee_filter != "ALL EMPLOYEES":
        sql_condition += " AND sold_by = %s"
        params.append(employee_filter)

    cash_revenue = 0
    total_credit = 0
    total_count = 0
    recent_sales = []
    total_outflows = 0
    recent_outflows = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'PAID'", tuple(params))
            cash_revenue = cur.fetchone()[0] or 0
        except Exception:
            cash_revenue = 0
        
        try:
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'CREDIT'", tuple(params))
            total_credit = cur.fetchone()[0] or 0
        except Exception:
            total_credit = 0
        
        cur.execute(f"SELECT COUNT(*) FROM sales {sql_condition}", tuple(params))
        total_count = cur.fetchone()[0] or 0
        
        try:
            cur.execute(f"SELECT item, price, sold_by, sale_time, payment_status, customer_name FROM sales {sql_condition} ORDER BY id DESC LIMIT 10", tuple(params))
            recent_sales = cur.fetchall()
        except Exception:
            recent_sales = []

        cur.execute(f"SELECT SUM(amount) FROM safe_outflows {outflow_condition}", tuple(outflow_params))
        total_outflows = cur.fetchone()[0] or 0

        cur.execute(f"SELECT reason, amount, logged_by, time_logged FROM safe_outflows {outflow_condition} ORDER BY id DESC LIMIT 10", tuple(outflow_params))
        recent_outflows = cur.fetchall()

        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        
    return cash_revenue, total_credit, total_count, recent_sales, total_outflows, recent_outflows

# --- LOGIN CONTROL ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔒 Sammy Worx Portal")
    st.subheader("Admin Identity Verification")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Secure Login", use_container_width=True):
        if username == "admin" and password == "worx123":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Invalid Admin Credentials")
else:
    # --- DASHBOARD INTERFACE ---
    st.title("📊 Sammy Worx Management Panel")
    st.caption("Live Shop Credit, Outflows & Universal Print Station")

    employee_choice = st.selectbox("Filter Metrics by Employee:", ["ALL EMPLOYEES"] + STAFF_NAMES)
    time_tab = st.radio("Select Performance Timeframe:", ["Today", "This Week", "This Month"], horizontal=True)

    cash_collected, total_owed, order_count, recent_items, safe_outflows, recent_expenses = fetch_mobile_metrics(time_tab, employee_choice)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Cash Collected 💰", value=f"UGX {int(cash_collected):,}")
    with col2:
        st.metric(label="Total Owed Debt ⚠️", value=f"UGX {int(total_owed):,}")
        
    col3, col4 = st.columns(2)
    with col3:
        st.metric(label="Safe Cash Outflows 💸", value=f"UGX {int(safe_outflows):,}")
    with col4:
        st.metric(label="Transactions Logged", value=f"{order_count} Entries")

    st.markdown("---")
    
    # --- GLOBAL PRINT UTILITY STATION ---
    st.subheader("🖨️ Universal Print Station")
    st.write("Search any specific date below to pull up and print all sales records.")
    
    ug_tz = timezone(timedelta(hours=3))
    selected_print_date = st.date_input("Select Target Log Date to Print:", datetime.now(ug_tz))
    
    if st.button("🔍 Search & Generate Printable Statement", use_container_width=True):
        formatted_date = selected_print_date.strftime("%Y-%m-%d")
        print_data = fetch_all_sales_for_date(formatted_date)
        
        if not print_data:
            st.error(f"No transaction records found in the database for {formatted_date}.")
        else:
            st.success(f"Found {len(print_data)} transactions! Scroll down and click the 'Print Report' button below.")
            
            # Formulate Clean HTML Page structure with built-in Print Action Button
            report_html = f"""
            <style>
                @media print {{
                    .no-print {{
                        display: none !important;
                    }}
                    #print-area {{
                        padding: 0px !important;
                    }}
                }}
                .print-btn {{
                    background-color: #2e7d32;
                    color: white;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    margin-bottom: 20px;
                    display: block;
                    text-align: center;
                }}
                .print-btn:hover {{
                    background-color: #1b5e20;
                }}
            </style>

            <button class="print-btn no-print" onclick="window.print();">🖨️ CLICK HERE TO PRINT THIS REPORT</button>

            <div id="print-area" style="font-family: 'Segoe UI', Arial, sans-serif; color: black; padding: 10px; background-color: white;">
                <div style="text-align: center; border-bottom: 2px solid black; padding-bottom: 10px;">
                    <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">SAMMY WORX PRINTS & DESIGN</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px; text-transform: uppercase; color: #333;">Official Daily Sales Statement</p>
                </div>
                
                <div style="margin-top: 15px; font-size: 14px;">
                    <p><b>Statement Date:</b> {formatted_date}</p>
                    <p><b>Generated On:</b> {datetime.now(ug_tz).strftime('%Y-%m-%d %H:%M:%S')} EAT</p>
                </div>
                
                <table style="width:100%; border-collapse: collapse; margin-top: 20px; font-size: 13px;">
                    <thead>
                        <tr style="background-color: #f2f2f2; border-bottom: 2px solid black; text-align: left;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Time</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Item Description</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Handled By</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Client Name</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            grand_total = 0
            for row in print_data:
                item, price, sold_by, sale_time, status, customer = row
                client_name = customer if customer else "Walk-in"
                grand_total += price
                
                status_color = "green" if status == "PAID" else "red"
                
                report_html += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; border: 1px solid #ddd;">{sale_time}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>{item}</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{sold_by}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{client_name}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{status}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">UGX {int(price):,}</td>
                    </tr>
                """
            
            report_html += f"""
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; text-align: right; border-top: 2px solid black; padding-top: 10px;">
                    <h2 style="margin: 0;">Grand Total Sales: UGX {int(grand_total):,}</h2>
                </div>
                
                <div style="margin-top: 50px; text-align: center; font-size: 11px; color: #777; border-top: 1px dashed #ccc; padding-top: 10px;">
                    Thank you for partnering with Sammy Worx Prints & Design. All system logs are securely preserved on TiDB Cloud.
                </div>
            </div>
            """
            st.components.v1.html(report_html, height=600, scrolling=True)

    st.markdown("---")
    
    # Navigation Tabs for the Main Activity Feeds
    feed_tab = st.tabs(["📝 Live Sales & Debt Feed", "💸 Safe Drawer Outflows"])

    with feed_tab[0]:
        view_filter = st.selectbox("Transaction Log Filter:", ["Show All Records", "Unpaid Credit Only", "Paid Cash Only"])
        st.subheader("Activity & Debt Entries")

        if not recent_items:
            st.info("No records found matching these filters.")
        else:
            displayed_any = False
            for row in recent_items:
                item_name, price, sold_by, sale_time, status, customer = row
                if view_filter == "Unpaid Credit Only" and status != "CREDIT":
                    continue
                if view_filter == "Paid Cash Only" and status != "PAID":
                    continue
                displayed_any = True
                
                if status == "CREDIT":
                    st.markdown(f"> 🔴 **CREDIT UNPAID**\n> **🛍️ Item:** {item_name}\n> **👤 Customer Debt Issued To:** `{customer.upper()}`\n> **💰 Value:** `UGX {int(price):,}` | **By:** {str(sold_by).upper()} at {sale_time}")
                else:
                    client_name = customer if customer else "Walk-in"
                    st.markdown(f"🟢 **PAID CASH**\n**🛍️ Item:** {item_name} | **Client:** {client_name}\n`UGX {int(price):,}` | **By:** {str(sold_by).upper()} at {sale_time}")
                st.markdown("---")
                
            if not displayed_any:
                st.info("No matching records inside this timeframe for the selected view option.")

    with feed_tab[1]:
        st.subheader("Safe Outflow History")
        if not recent_expenses:
            st.info("No safe drawer cash outflows recorded inside this timeframe.")
        else:
            for expense in recent_expenses:
                reason, amount, logged_by, time_logged = expense
                st.markdown(f"> 💸 **SAFE CASH TAKEN**\n> **📌 Reason/Use:** {reason}\n> **💰 Amount:** `UGX {int(amount):,}`\n> **👤 Authorized By:** {str(logged_by).upper()} at {time_logged}")
                st.markdown("---")
                
    if st.button("Log Out", type="secondary"):
        st.session_state['authenticated'] = False
        st.rerun()