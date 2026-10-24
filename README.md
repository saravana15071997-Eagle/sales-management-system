# Sales Management System

## Project Overview

The Sales Management System is a web-based application developed using Python, Streamlit, and MySQL. It is designed to manage customer sales, branch-wise transactions, payment records, and outstanding balances.

## Features

- **Role-Based Login:** Separate access for Super Admin and Admin users.
- **Branch-Wise Access:** Admin users can access records for their assigned branch.
- **Customer Sales Management:** View and manage customer sales records.
- **Payment Tracking:** Record and track customer payments, including split payments.
- **Automatic Balance Calculation:** Calculate pending balances using a MySQL generated column.
- **Database Triggers:** Update received amounts and sales status when payment records change.
- **Dashboard KPIs:** Display total sales, received amounts, pending balances, and customer counts.
- **SQL Reports:** Execute predefined SQL queries for business analysis.

## Technologies Used

- Python
- Streamlit
- MySQL
- MySQL Connector for Python
- Pandas
- SQL

## Database Tables

- `branches`
- `users`
- `customer_sales`
- `payment_splits`

## How to Run

1. Install Python and MySQL.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the database and tables in MySQL.
4. Configure the database connection in `db.py`.
5. Start the Streamlit application:

   ```bash
   streamlit run app.py
   ```



## Project Objective

To develop a database-driven sales management application with branch-wise access control, automated payment calculations, and SQL-based reporting.

## Project Status

In Development
