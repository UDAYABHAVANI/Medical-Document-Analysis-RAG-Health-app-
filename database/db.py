import pyodbc
from flask import g


def get_db():
    if 'db' not in g:
        # Use the server name found in image_8787a9.png
        conn_str = (
            "Driver={SQL Server};"
            "Server=.;"
            "Database=healthapp_db;"
            "Trusted_Connection=yes;"
        )
        try:
            g.db = pyodbc.connect(conn_str)
        except pyodbc.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise e
    return g.db
