import streamlit as st
import pandas as pd
from datetime import date
from db import create_connection
from sql_reports import sql_analysis

st.set_page_config(page_title="Sales Management System", page_icon="💼", layout="wide")


def fetch_all(query, params=()):
    conn = create_connection()
    if conn is None:
        st.error("Database connection failed. Check db.py and MySQL.")
        return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as exc:
        st.error(f"Database error: {exc}")
        return []
    finally:
        if cursor:
            cursor.close()
        conn.close()


def execute_write(query, params=()):
    conn = create_connection()
    if conn is None:
        st.error("Database connection failed. Check db.py and MySQL.")
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        st.error(f"Database error: {exc}")
        return False
    finally:
        if cursor:
            cursor.close()
        conn.close()


def get_branches():
    return fetch_all("SELECT branch_id, branch_name, branch_admin_name FROM branches ORDER BY branch_name")


def get_products(user, branch_id=None):
    query = "SELECT DISTINCT product_name FROM customer_sales WHERE product_name IS NOT NULL AND product_name <> ''"
    params = []
    if user["role"] != "Super Admin":
        query += " AND branch_id = %s"
        params.append(user["branch_id"])
    elif branch_id is not None:
        query += " AND branch_id = %s"
        params.append(branch_id)
    query += " ORDER BY product_name"
    return [row["product_name"] for row in fetch_all(query, tuple(params))]


def get_sales(user, branch_id=None, product="All", start_date=None, end_date=None, status="All", search=""):
    query = """SELECT cs.sale_id, cs.branch_id, b.branch_name, cs.date, cs.name, cs.mobile_number,
        cs.product_name, cs.gross_sales, cs.received_amount, cs.pending_amount, cs.status
        FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id WHERE 1=1"""
    params = []
    if user["role"] != "Super Admin":
        query += " AND cs.branch_id = %s"
        params.append(user["branch_id"])
    elif branch_id is not None:
        query += " AND cs.branch_id = %s"
        params.append(branch_id)
    if product != "All":
        query += " AND cs.product_name = %s"
        params.append(product)
    if start_date:
        query += " AND cs.date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND cs.date <= %s"
        params.append(end_date)
    if status != "All":
        query += " AND cs.status = %s"
        params.append(status)
    if search.strip():
        pattern = f"%{search.strip()}%"
        query += " AND (cs.name LIKE %s OR cs.mobile_number LIKE %s OR cs.product_name LIKE %s)"
        params.extend([pattern, pattern, pattern])
    query += " ORDER BY cs.sale_id DESC"
    return fetch_all(query, tuple(params))


def get_payments(user):
    query = """SELECT ps.payment_id, ps.sale_id, ps.payment_date, ps.amount_paid,
        ps.payment_method, cs.name AS customer_name, b.branch_name
        FROM payment_splits ps JOIN customer_sales cs ON cs.sale_id = ps.sale_id
        JOIN branches b ON b.branch_id = cs.branch_id"""
    params = []
    if user["role"] != "Super Admin":
        query += " WHERE cs.branch_id = %s"
        params.append(user["branch_id"])
    query += " ORDER BY ps.payment_id DESC"
    return fetch_all(query, tuple(params))


def login():
    st.title("Sales Management System")
    st.header("Welcome to the Super admin Login Page")
    st.info("Please login to check the customer sales report")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        users = fetch_all("""SELECT user_id, username, password, branch_id, role, email
            FROM users WHERE username = %s AND password = %s LIMIT 1""", (username.strip(), password))
        if users:
            st.session_state.logged_in = True
            st.session_state.user = users[0]
            st.session_state.page = "Dashboard & Reports"
            st.rerun()
        else:
            st.error("Invalid username or password")


def dashboard_page(user):
    """Dashboard shown when Dashboard & Reports is selected in the sidebar."""
    st.title("📈 Sales Management System")
    st.subheader("🔎 Filter Controls")

    branches = get_branches()
    if user["role"] == "Super Admin":
        branch_options = {"All": None}
        for branch in branches:
            branch_options[branch["branch_name"]] = branch["branch_id"]
        branch_name = st.selectbox("Branch Name", list(branch_options.keys()), key="dashboard_branch")
        branch_id = branch_options[branch_name]
    else:
        branch_id = user["branch_id"]
        branch_name = next(
            (branch["branch_name"] for branch in branches if branch["branch_id"] == branch_id),
            "Your Branch",
        )
        st.text_input("Branch Name", value=branch_name, disabled=True, key="dashboard_branch_admin")

    products = ["All"] + get_products(user, branch_id)
    filter_cols = st.columns(4)
    with filter_cols[0]:
        product = st.selectbox("Product Name", products, key="dashboard_product")
    with filter_cols[1]:
        start_date = st.date_input("Start Date", value=date(2024, 1, 1), key="dashboard_start_date")
    with filter_cols[2]:
        end_date = st.date_input("End Date", value=date.today(), key="dashboard_end_date")
    with filter_cols[3]:
        status = st.selectbox("Status", ["All", "Open", "Close"], key="dashboard_status")

    search = st.text_input("Search customer, mobile number or product", key="dashboard_search")
    if start_date > end_date:
        st.error("Start Date cannot be later than End Date.")
        return

    sales = get_sales(user, branch_id, product, start_date, end_date, status, search)
    gross = sum(float(row["gross_sales"] or 0) for row in sales)
    received = sum(float(row["received_amount"] or 0) for row in sales)
    pending = sum(float(row["pending_amount"] or 0) for row in sales)
    pending_pct = pending / gross * 100 if gross else 0

    st.divider()
    st.subheader("💵 Financial Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Overall Revenue (Gross)", f"₹{gross:,.2f}")
    k2.metric("Total Received Amount", f"₹{received:,.2f}")
    k3.metric("Total Pending Amount", f"₹{pending:,.2f}")
    k4.metric("Pending Collection Pct", f"{pending_pct:.1f}%")

    st.divider()
    st.subheader("🏢 Branch Sales Records Summary")
    if sales:
        sales_df = pd.DataFrame(sales)
        branch_summary = (
            sales_df.groupby(["branch_id", "branch_name"], as_index=False)
            .agg(
                total_sales=("sale_id", "count"),
                gross_sales=("gross_sales", "sum"),
                received_amount=("received_amount", "sum"),
                pending_amount=("pending_amount", "sum"),
            )
            .sort_values("branch_name")
        )
        st.dataframe(branch_summary, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📋 Customer Sales Report")
        display_df = sales_df.rename(columns={
            "date": "sale_date",
            "name": "customer_name",
            "mobile_number": "customer_mobile_number",
        })
        wanted_columns = [
            "sale_id", "branch_id", "branch_name", "sale_date", "customer_name",
            "customer_mobile_number", "product_name", "gross_sales", "received_amount",
            "pending_amount", "status",
        ]
        display_df = display_df[[column for column in wanted_columns if column in display_df.columns]].copy()
        for column in ["gross_sales", "received_amount", "pending_amount"]:
            if column in display_df.columns:
                display_df[column] = pd.to_numeric(display_df[column], errors="coerce").fillna(0)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=520)
        st.caption(f"Records displayed: {len(display_df):,}")
    else:
        st.info("No sales records found for the selected filters.")


def data_entry_page(user):
    st.title("📝 Operations Record Creator")
    sale_tab, payment_tab = st.tabs(["Add New Sales Entry", "Log Payment Split Details"])
    branches = get_branches()

    with sale_tab:
        st.subheader("New Sale Generation")
        with st.form("new_sale_form", clear_on_submit=True):
            if user["role"] == "Super Admin":
                branch_options = {b["branch_name"]: b["branch_id"] for b in branches}
                branch_name = st.selectbox("Select Target Branch", list(branch_options.keys()))
                branch_id = branch_options[branch_name]
            else:
                branch_id = user["branch_id"]
                branch_name = next((b["branch_name"] for b in branches if b["branch_id"] == branch_id), "Your Branch")
                st.text_input("Select Target Branch", value=branch_name, disabled=True)
            left, right = st.columns(2)
            with left:
                customer_name = st.text_input("Customer Name")
                mobile = st.text_input("Mobile Number")
            with right:
                product_name = st.text_input("Product Name")
                sale_date = st.date_input("Sale Date", value=date.today())
            gross = st.number_input("Gross Sales Amount (₹)", min_value=0.0, step=100.0)
            initial_received = st.number_input("Initial Received Amount (₹)", min_value=0.0, step=100.0)
            status = st.selectbox("Initial Order Status", ["Open", "Close"])
            save_sale = st.form_submit_button("Publish Sale Entry")
        if save_sale:
            if not customer_name.strip() or not mobile.strip() or not product_name.strip():
                st.error("Customer, mobile number and product are required.")
            elif gross <= 0:
                st.error("Gross Sales must be greater than zero.")
            elif initial_received > gross:
                st.error("Received amount cannot exceed gross sales.")
            else:
                ok = execute_write("""INSERT INTO customer_sales
                    (branch_id, `date`, name, mobile_number, product_name, gross_sales, received_amount, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (branch_id, sale_date, customer_name.strip(), mobile.strip(), product_name.strip(), gross, initial_received, status))
                if ok:
                    st.success("Sale entry saved successfully.")
                    st.rerun()

    with payment_tab:
        st.subheader("Post Payment Installment Split")
        query = """SELECT cs.sale_id, cs.name, cs.branch_id, b.branch_name, cs.gross_sales,
            cs.received_amount, cs.pending_amount FROM customer_sales cs
            JOIN branches b ON b.branch_id = cs.branch_id WHERE cs.pending_amount > 0"""
        params = []
        if user["role"] != "Super Admin":
            query += " AND cs.branch_id = %s"
            params.append(user["branch_id"])
        query += " ORDER BY cs.sale_id DESC"
        available = fetch_all(query, tuple(params))
        if not available:
            st.info("No sales with pending amounts are available.")
        else:
            options = {f'ID {r["sale_id"]} - {r["name"]} ({r["branch_name"]}) - ₹{float(r["pending_amount"]):,.2f} pending': r for r in available}
            with st.form("payment_form", clear_on_submit=True):
                selected_label = st.selectbox("Select Target Sale", list(options.keys()))
                sale = options[selected_label]
                st.caption(f'Gross: ₹{float(sale["gross_sales"]):,.2f} | Received: ₹{float(sale["received_amount"]):,.2f} | Pending: ₹{float(sale["pending_amount"]):,.2f}')
                method = st.selectbox("Payment Collection Channel", ["Cash", "UPI", "Bank Transfer", "Cheque", "Other"])
                amount = st.number_input("Payment Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
                payment_date = st.date_input("Payment Date", value=date.today())
                save_payment = st.form_submit_button("Apply Payment Allocation")
            if save_payment:
                if amount > float(sale["pending_amount"]):
                    st.error("Payment cannot exceed pending amount.")
                else:
                    ok = execute_write("""INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                        VALUES (%s,%s,%s,%s)""", (sale["sale_id"], payment_date, amount, method))
                    if ok:
                        st.success("Payment saved successfully. The database trigger should update the sale totals.")
                        st.rerun()

    st.divider()
    st.subheader("💳 Existing Payment Split Records")
    payments = get_payments(user)
    if payments:
        df = pd.DataFrame([{
            "payment_id": p["payment_id"], "sale_id": p["sale_id"], "branch": p["branch_name"],
            "customer": p["customer_name"], "payment_date": p["payment_date"],
            "amount_paid": float(p["amount_paid"] or 0), "payment_method": p["payment_method"]
        } for p in payments])
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No payment records found.")


def sql_engine_page(user):
    sql_analysis(user)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard & Reports"

if not st.session_state.logged_in:
    login()
else:
    user = st.session_state.user
    pages = ["Dashboard & Reports", "Data Entry Workspace", "Advanced SQL Engine"]
    with st.sidebar:
        st.title("Navigation")
        selected = st.radio("Go to", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
        st.session_state.page = selected
        st.divider()
        st.write(f'👤 **User:** {user["username"]}')
        st.write(f'🔑 **Role:** {user["role"]}')
        if user["role"] != "Super Admin":
            branches = get_branches()
            own_branch = next((b["branch_name"] for b in branches if b["branch_id"] == user["branch_id"]), "Your Branch")
            st.write(f"🏢 **Branch:** {own_branch}")
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "Dashboard & Reports"
            st.rerun()

    if selected == "Dashboard & Reports":
        dashboard_page(user)
    elif selected == "Data Entry Workspace":
        data_entry_page(user)
    else:
        sql_engine_page(user)
