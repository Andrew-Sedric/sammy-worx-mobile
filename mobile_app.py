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

# DATABASE INITIALIZATION: Create safe_outflows table if it does not exist
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

# Run database setup check
initialize_database()

# Extract mobile metrics matching timeframe + employee selection + debt fields
def fetch_mobile_metrics(filter_mode, employee_filter):
    # FORCE UGANDA TIMEZONE (UTC+3) to match shop desktop logging perfectly
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

    # Apply staff filtering strictly to sales performance
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
        
        # 1. Fetch Cash Revenue (PAID status items only)
        try:
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'PAID'", tuple(params))
            cash_revenue = cur.fetchone()[0] or 0
        except Exception:
            cash_revenue = 0
        
        # 2. Fetch Outstanding Credit Debts (CREDIT status items only)
        try:
            cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'CREDIT'", tuple(params))
            total_credit = cur.fetchone()[0] or 0
        except Exception:
            total_credit = 0
        
        # 3. Fetch Combined Transaction Counts
        cur.execute(f"SELECT COUNT(*) FROM sales {sql_condition}", tuple(params))
        total_count = cur.fetchone()[0] or 0
        
        # 4. Fetch Last 10 Transactions including Customer names & Payment Status
        try:
            cur.execute(f"SELECT item, price, sold_by, sale_time, payment_status, customer_name FROM sales {sql_condition} ORDER BY id DESC LIMIT 10", tuple(params))
            recent_sales = cur.fetchall()
        except Exception:
            recent_sales = []

        # 5. Fetch Total Safe Cash Outflows (Universal view for admin tracking)
        cur.execute(f"SELECT SUM(amount) FROM safe_outflows {outflow_condition}", tuple(outflow_params))
        total_outflows = cur.fetchone()[0] or 0

        # 6. Fetch Last 10 Safe Cash Outflows details
        cur.execute(f"SELECT reason, amount, logged_by, time_logged FROM safe_outflows {outflow_condition} ORDER BY id DESC LIMIT 10", tuple(outflow_params))
        recent_outflows = cur.fetchall()

        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        
    return cash_revenue, total_credit, total_count, recent_sales, total_outflows, recent_outflows

# --- SIMPLE SECURE MOBILE LOGIN ---
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
    # --- MOBILE DASHBOARD INTERFACE ---
    st.title("📊 Sammy Worx Mobile")
    st.caption("Live Shop Credit, Outflows & Sales Performance Monitor")

    # Mobile Dropdown Filter for Staff Selection
    employee_choice = st.selectbox("Filter by Employee:", ["ALL EMPLOYEES"] + STAFF_NAMES)
    
    # Touch-friendly Timeframe Tabs
    time_tab = st.radio("Select Timeframe:", ["Today", "This Week", "This Month"], horizontal=True)

    # Fetch Data Based on Mobile Toggles
    cash_collected, total_owed, order_count, recent_items, safe_outflows, recent_expenses = fetch_mobile_metrics(time_tab, employee_choice)

    st.markdown("---")

    # Clean Touch-friendly Big Metric Cards
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
    
    # Navigation Tabs for the Activity Feeds
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
                    st.markdown(
                        f"""
                        > 🔴 **CREDIT UNPAID**
                        > **🛍️ Item:** {item_name}
                        > **👤 Customer Debt Issued To:** `{customer.upper()}`
                        > **💰 Value:** `UGX {int(price):,}` | **By:** {str(sold_by).upper()} at {sale_time}
                        """
                    )
                else:
                    client_name = customer if customer else "Walk-in"
                    st.markdown(
                        f"""
                        🟢 **PAID CASH**
                        **🛍️ Item:** {item_name} | **Client:** {client_name}
                        `UGX {int(price):,}` | **By:** {str(sold_by).upper()} at {sale_time}
                        """
                    )
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
                st.markdown(
                    f"""
                    > 💸 **SAFE CASH TAKEN**
                    > **📌 Reason/Use:** {reason}
                    > **💰 Amount:** `UGX {int(amount):,}`
                    > **👤 Authorized By:** {str(logged_by).upper()} at {time_logged}
                    """
                )
                st.markdown("---")
                
    if st.button("Log Out", type="secondary"):
        st.session_state['authenticated'] = False
        st.rerun()