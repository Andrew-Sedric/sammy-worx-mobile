import streamlit as st
import pymysql
from datetime import datetime, timedelta, timezone

# Configure mobile page layout
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

# Fetch all sales for a single targeted day (unlimited rows for printing)
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
    st.title("📊 Sammy Worx Mobile")
    st.caption("Live Shop Credit, Outflows & Sales Performance Monitor")

    employee_choice = st.selectbox("Filter by Employee:", ["ALL EMPLOYEES"] + STAFF_NAMES)
    time_tab = st.radio("Select Timeframe:", ["Today", "This Week", "This Month"], horizontal=True)

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
    
    # --- PRINT FEATURE SECTION ---
    st.subheader("🖨️ Print Daily Statements")
    ug_tz = timezone(timedelta(hours=3))
    selected_print_date = st.date_input("Select Date to Print:", datetime.now(ug_tz))
    
    if st.button("🖨️ Prepare Printable Report", use_container_width=True):
        formatted_date = selected_print_date.strftime("%Y-%m-%d")
        print_data = fetch_all_sales_for_date(formatted_date)
        
        if not print_data:
            st.warning(f"No transactions found for {formatted_date} to print.")
        else:
            # Create clear clean HTML structure for paper printing
            report_html = f"""
            <div id="print-area" style="font-family: Arial, sans-serif; color: black; padding: 10px;">
                <h2 style="text-align: center; margin-bottom: 5px;">SAMMY WORX PRINTS & DESIGN</h2>
                <h4 style="text-align: center; margin-top: 0; color: #555;">DAILY SALES STATEMENT</h4>
                <p><b>Date Covered:</b> {formatted_date}</p>
                <hr style="border: 1px solid black;"/>
                <table style="width:100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="border-bottom: 2px solid black; text-align: left;">
                            <th style="padding: 8px;">Time</th>
                            <th style="padding: 8px;">Item Description</th>
                            <th style="padding: 8px;">Client</th>
                            <th style="padding: 8px;">Status</th>
                            <th style="padding: 8px; text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            grand_total = 0
            for row in print_data:
                item, price, sold_by, sale_time, status, customer = row
                client_name = customer if customer else "Walk-in"
                grand_total += price
                report_html += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px;">{sale_time}</td>
                        <td style="padding: 8px;">{item} <br><small style="color:#666;">By: {sold_by}</small></td>
                        <td style="padding: 8px;">{client_name}</td>
                        <td style="padding: 8px;"><b>{status}</b></td>
                        <td style="padding: 8px; text-align: right;">UGX {int(price):,}</td>
                    </tr>
                """
            
            report_html += f"""
                    </tbody>
                </table>
                <hr style="border: 1px solid black; margin-top: 20px;"/>
                <h3 style="text-align: right;">Grand Total Sales: UGX {int(grand_total):,}</h3>
            </div>
            <script>
                // Instantly call device system print window
                var win = window.open('', '', 'height=700,width=900');
                win.document.write('<html><head><title>Print Report</title></head><body>');
                win.document.write(document.getElementById('print-area').innerHTML);
                win.document.write('</body></html>');
                win.document.close();
                win.print();
            </script>
            """
            # Render the printable sheet container directly to web app output
            st.components.v1.html(report_html, height=450, scrolling=True)

    st.markdown("---")
    
    # Navigation Tabs for the Main Activity Feeds
    feed_tab = st.tabs(["📝 Sales & Debt Feed", "💸 Safe Drawer Outflows"])

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