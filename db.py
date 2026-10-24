import os
import mysql.connector


def create_connection():
    password = os.getenv("MYSQL_PASSWORD")

    if not password:
        raise ValueError(
            "MYSQL_PASSWORD environment variable is not configured."
        )

    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=password,
        database=os.getenv(
            "MYSQL_DATABASE",
            "sales_management_system"
        )
    )

    return connection
    
