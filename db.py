import mysql.connector


def create_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sales_management_system"
    )

    return connection