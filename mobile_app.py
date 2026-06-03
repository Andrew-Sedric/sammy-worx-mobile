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

# Extract mobile metrics matching timeframe + employee selection
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

    total_revenue = 0
    total_count = 0
    recent_sales = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch Summary Totals
        cur.execute(f"SELECT SUM(price), COUNT(*) FROM sales {sql_condition}", tuple(params))
        res = cur.fetchone()
        total_revenue = res[0] or 0
        total_count = res[1] or 0
        
        # 2. Fetch Last 5 Transactions for Mobile Monitoring
        cur.execute(f"SELECT item, price, sold_by, sale_time FROM sales {sql_condition} ORDER BY id DESC LIMIT 5", tuple(params))
        recent_sales = cur.fetchall()

        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        
    return total_revenue, total_count, recent_sales

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
    st.caption("Live Shop Performance Monitor")

    # Mobile Dropdown Filter for Staff Selection
    employee_choice = st.selectbox("Filter by Employee:", ["ALL EMPLOYEES"] + STAFF_NAMES)
    
    # Touch-friendly Timeframe Tabs
    time_tab = st.radio("Select Timeframe:", ["Today", "This Week", "This Month"], horizontal=True)

    # Fetch Data Based on Mobile Toggles
    revenue, order_count, recent_items = fetch_mobile_metrics(time_tab, employee_choice)

    st.markdown("---")

    # Clean Touch-friendly Big Metric Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Revenue", value=f"UGX {int(revenue):,}")
    with col2:
        st.metric(label="Orders Closed", value=f"{order_count} Sales")

    st.markdown("---")
    st.subheader("📝 Recent Transactions Log")

    # Render a clean feed layout optimized for vertical phone viewing
    if not recent_items:
        st.info("No sales found matching these filters.")
    else:
        for row in recent_items:
            with st.container():
                st.markdown(
                    f"""
                    **🛍️ {row[0]}** * Value: `UGX {int(row[1]):,}` | By: **{str(row[2]).upper()}** | Time: *{row[3]}*
                    """
                )
                st.markdown("---")
                
    if st.button("Log Out", type="secondary"):
        st.session_state['authenticated'] = False
        st.rerun()