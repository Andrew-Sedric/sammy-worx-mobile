import streamlit as st
import pymysql
from datetime import datetime, timedelta

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

# Extract mobile metrics matching timeframe + employee selection + debt fields
def fetch_mobile_metrics(filter_mode, employee_filter):
    today = datetime.now().strftime("%Y-%m-%d")
    
    if filter_mode == "Today":
        sql_condition = "WHERE sale_date = %s"
        params = [today]
    elif filter_mode == "This Week":
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        sql_condition = "WHERE sale_date >= %s"
        params = [week_ago]
    else:
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        sql_condition = "WHERE sale_date >= %s"
        params = [month_ago]

    if employee_filter != "ALL EMPLOYEES":
        sql_condition += " AND sold_by = %s"
        params.append(employee_filter)

    cash_revenue = 0
    total_credit = 0
    total_count = 0
    recent_sales = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch Cash Revenue (PAID status items only)
        cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'PAID'", tuple(params))
        cash_revenue = cur.fetchone()[0] or 0
        
        # 2. Fetch Outstanding Credit Debts (CREDIT status items only)
        cur.execute(f"SELECT SUM(price) FROM sales {sql_condition} AND payment_status = 'CREDIT'", tuple(params))
        total_credit = cur.fetchone()[0] or 0
        
        # 3. Fetch Combined Transaction Counts
        cur.execute(f"SELECT COUNT(*) FROM sales {sql_condition}", tuple(params))
        total_count = cur.fetchone()[0] or 0
        
        # 4. Fetch Last 10 Transactions including Customer names & Payment Status
        cur.execute(f"SELECT item, price, sold_by, sale_time, payment_status, customer_name FROM sales {sql_condition} ORDER BY id DESC LIMIT 10", tuple(params))
        recent_sales = cur.fetchall()

        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        
    return cash_revenue, total_credit, total_count, recent_sales

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
    st.caption("Live Shop Credit & Sales Performance Monitor")

    # Mobile Dropdown Filter for Staff Selection
    employee_choice = st.selectbox("Filter by Employee:", ["ALL EMPLOYEES"] + STAFF_NAMES)
    
    # Touch-friendly Timeframe Tabs
    time_tab = st.radio("Select Timeframe:", ["Today", "This Week", "This Month"], horizontal=True)

    # Fetch Data Based on Mobile Toggles
    cash_collected, total_owed, order_count, recent_items = fetch_mobile_metrics(time_tab, employee_choice)

    st.markdown("---")

    # Clean Touch-friendly Big Metric Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Cash Collected 💰", value=f"UGX {int(cash_collected):,}")
    with col2:
        st.metric(label="Total Owed Debt ⚠️", value=f"UGX {int(total_owed):,}")
        
    st.metric(label="Total Transactions Logged", value=f"{order_count} Entries")

    st.markdown("---")
    
    # Quick filter for transaction types on mobile
    view_filter = st.selectbox("Transaction Log Filter:", ["Show All Records", "Unpaid Credit Only", "Paid Cash Only"])
    
    st.subheader("📝 Activity & Debt Feed")

    # Render a clean feed layout optimized for vertical phone viewing
    if not recent_items:
        st.info("No records found matching these filters.")
    else:
        displayed_any = False
        for row in recent_items:
            item_name, price, sold_by, sale_time, status, customer = row
            
            # Apply the log viewing filter toggles
            if view_filter == "Unpaid Credit Only" and status != "CREDIT":
                continue
            if view_filter == "Paid Cash Only" and status != "PAID":
                continue
                
            displayed_any = True
            
            # Color indicator and design text depending on payment status
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
                st.markdown(
                    f"""
                    🟢 **PAID CASH**
                    **🛍️ Item:** {item_name} | **Client:** {customer}
                    `UGX {int(price):,}` | **By:** {str(sold_by).upper()} at {sale_time}
                    """
                )
            st.markdown("---")
            
        if not displayed_any:
            st.info("No matching records inside this timeframe for the selected view option.")
                
    if st.button("Log Out", type="secondary"):
        st.session_state['authenticated'] = False
        st.rerun()