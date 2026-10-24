import pandas as pd
import streamlit as st
from db import create_connection


def _execute_read_query(query, params=()):
    """Execute a predefined read-only SQL query and return dictionary rows."""
    conn = create_connection()
    if conn is None:
        raise RuntimeError("Could not connect to the MySQL database.")
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        conn.close()


def _query_catalog(branch_id=None):
    """Return the 20 predefined reports. Branch admins are scoped to their branch."""
    scoped_cs = " WHERE cs.branch_id = %s" if branch_id is not None else ""
    scoped_sales = " WHERE branch_id = %s" if branch_id is not None else ""
    scoped_ps = " WHERE cs.branch_id = %s" if branch_id is not None else ""
    p = (branch_id,) if branch_id is not None else ()

    # Each item is (SQL, parameters). Every query is read-only and predefined.
    return {
        "1. Retrieve all customer sales": (
            "SELECT cs.sale_id, cs.branch_id, b.branch_name, cs.date, cs.name, "
            "cs.mobile_number, cs.product_name, cs.gross_sales, cs.received_amount, "
            "cs.pending_amount, cs.status FROM customer_sales cs "
            "JOIN branches b ON b.branch_id = cs.branch_id" + scoped_cs + " ORDER BY cs.sale_id", p),
        "2. Retrieve all branches": (
            "SELECT branch_id, branch_name, branch_admin_name FROM branches" +
            (" WHERE branch_id = %s" if branch_id is not None else "") + " ORDER BY branch_id",
            (branch_id,) if branch_id is not None else ()),
        "3. Retrieve all payment splits": (
            "SELECT ps.payment_id, ps.sale_id, cs.branch_id, b.branch_name, cs.name AS customer_name, "
            "ps.payment_date, ps.amount_paid, ps.payment_method FROM payment_splits ps "
            "JOIN customer_sales cs ON cs.sale_id = ps.sale_id "
            "JOIN branches b ON b.branch_id = cs.branch_id" + scoped_ps + " ORDER BY ps.payment_id",
            p),
        "4. Display sales with status Open": (
            "SELECT cs.sale_id, b.branch_name, cs.date, cs.name, cs.mobile_number, cs.product_name, "
            "cs.gross_sales, cs.received_amount, cs.pending_amount, cs.status "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id "
            "WHERE cs.status = 'Open'" + (" AND cs.branch_id = %s" if branch_id is not None else "") +
            " ORDER BY cs.sale_id", p),
        "5. Retrieve sales belonging to Chennai branch": (
            "SELECT cs.sale_id, b.branch_name, cs.date, cs.name, cs.mobile_number, cs.product_name, "
            "cs.gross_sales, cs.received_amount, cs.pending_amount, cs.status "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id "
            "WHERE b.branch_name = %s" + (" AND cs.branch_id = %s" if branch_id is not None else "") +
            " ORDER BY cs.sale_id", ("Chennai", branch_id) if branch_id is not None else ("Chennai",)),
        "6. Calculate total gross sales": (
            "SELECT COALESCE(SUM(gross_sales), 0) AS total_gross_sales FROM customer_sales" + scoped_sales, p),
        "7. Calculate total received amount": (
            "SELECT COALESCE(SUM(received_amount), 0) AS total_received FROM customer_sales" + scoped_sales, p),
        "8. Calculate total pending amount": (
            "SELECT COALESCE(SUM(pending_amount), 0) AS total_pending FROM customer_sales" + scoped_sales, p),
        "9. Count sales per branch": (
            "SELECT b.branch_id, b.branch_name, COUNT(cs.sale_id) AS total_sales "
            "FROM branches b LEFT JOIN customer_sales cs ON cs.branch_id = b.branch_id " +
            ("WHERE b.branch_id = %s " if branch_id is not None else "") +
            "GROUP BY b.branch_id, b.branch_name ORDER BY b.branch_name", p),
        "10. Find average gross sales": (
            "SELECT COALESCE(AVG(gross_sales), 0) AS average_gross_sales FROM customer_sales" + scoped_sales, p),
        "11. Sales details with branch name": (
            "SELECT cs.sale_id, b.branch_name, cs.date, cs.name, cs.mobile_number, cs.product_name, "
            "cs.gross_sales, cs.received_amount, cs.pending_amount, cs.status "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id" + scoped_cs +
            " ORDER BY cs.sale_id", p),
        "12. Sales with total payments received": (
            "SELECT cs.sale_id, cs.name, b.branch_name, cs.gross_sales, cs.received_amount, "
            "COALESCE(SUM(ps.amount_paid), 0) AS payment_split_total, cs.pending_amount "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id "
            "LEFT JOIN payment_splits ps ON ps.sale_id = cs.sale_id" + scoped_cs +
            " GROUP BY cs.sale_id, cs.name, b.branch_name, cs.gross_sales, cs.received_amount, cs.pending_amount "
            "ORDER BY cs.sale_id", p),
        "13. Branch-wise total gross sales": (
            "SELECT b.branch_id, b.branch_name, COALESCE(SUM(cs.gross_sales), 0) AS total_gross_sales "
            "FROM branches b LEFT JOIN customer_sales cs ON cs.branch_id = b.branch_id " +
            ("WHERE b.branch_id = %s " if branch_id is not None else "") +
            "GROUP BY b.branch_id, b.branch_name ORDER BY total_gross_sales DESC", p),
        "14. Sales along with payment method": (
            "SELECT cs.sale_id, cs.name AS customer_name, b.branch_name, ps.payment_date, "
            "ps.amount_paid, ps.payment_method FROM payment_splits ps "
            "JOIN customer_sales cs ON cs.sale_id = ps.sale_id "
            "JOIN branches b ON b.branch_id = cs.branch_id" + scoped_ps + " ORDER BY cs.sale_id, ps.payment_id", p),
        "15. Sales with branch admin name": (
            "SELECT cs.sale_id, b.branch_name, b.branch_admin_name, cs.date, cs.name AS customer_name, "
            "cs.product_name, cs.gross_sales, cs.received_amount, cs.pending_amount "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id" + scoped_cs +
            " ORDER BY cs.sale_id", p),
        "16. Sales with pending amount greater than 5000": (
            "SELECT cs.sale_id, b.branch_name, cs.name, cs.mobile_number, cs.product_name, "
            "cs.gross_sales, cs.received_amount, cs.pending_amount FROM customer_sales cs "
            "JOIN branches b ON b.branch_id = cs.branch_id WHERE cs.pending_amount > 5000" +
            (" AND cs.branch_id = %s" if branch_id is not None else "") + " ORDER BY cs.pending_amount DESC", p),
        "17. Top 3 highest gross sales": (
            "SELECT cs.sale_id, b.branch_name, cs.name, cs.product_name, cs.gross_sales "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id" + scoped_cs +
            " ORDER BY cs.gross_sales DESC LIMIT 3", p),
        "18. Branch with highest total gross sales": (
            "SELECT b.branch_id, b.branch_name, SUM(cs.gross_sales) AS total_gross_sales "
            "FROM customer_sales cs JOIN branches b ON b.branch_id = cs.branch_id " +
            ("WHERE cs.branch_id = %s " if branch_id is not None else "") +
            "GROUP BY b.branch_id, b.branch_name ORDER BY total_gross_sales DESC LIMIT 1", p),
        "19. Monthly sales summary": (
            "SELECT YEAR(cs.date) AS sales_year, MONTH(cs.date) AS sales_month, "
            "COUNT(*) AS number_of_sales, SUM(cs.gross_sales) AS total_gross_sales, "
            "SUM(cs.received_amount) AS total_received, SUM(cs.pending_amount) AS total_pending "
            "FROM customer_sales cs" + scoped_cs +
            " GROUP BY YEAR(cs.date), MONTH(cs.date) ORDER BY sales_year, sales_month", p),
        "20. Payment method-wise total collection": (
            "SELECT ps.payment_method, SUM(ps.amount_paid) AS total_collection, COUNT(*) AS payment_count "
            "FROM payment_splits ps JOIN customer_sales cs ON cs.sale_id = ps.sale_id" + scoped_ps +
            " GROUP BY ps.payment_method ORDER BY total_collection DESC", p),
    }


def sql_analysis(user):
    st.title("💻 Live SQL Business Analytics Engine")
    st.write("Select one of the 20 predefined SQL questions, then click Execute SQL Query to display its result as a table.")

    # Enforce branch scoping inside the query catalog for non-superadmins.
    branch_id = None if user.get("role") == "Super Admin" else user.get("branch_id")
    queries = _query_catalog(branch_id)

    selected_question = st.selectbox(
        "Select SQL Question",
        list(queries.keys()),
        key="sql_report_question"
    )

    if st.button("▶ Execute SQL Query", type="primary", key="execute_sql_report"):
        query, params = queries[selected_question]
        try:
            rows = _execute_read_query(query, params)
            if rows:
                df = pd.DataFrame(rows)
                st.subheader("📊 Query Results")
                st.dataframe(df, use_container_width=True, hide_index=True, height=520)
                st.caption(f"Total records: {len(df):,}")
            else:
                st.info("The selected query returned no records.")
        except Exception as exc:
            st.error(f"Unable to execute this report: {exc}")
