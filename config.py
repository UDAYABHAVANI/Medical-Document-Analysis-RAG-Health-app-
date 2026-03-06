import os


class Config:
    # Use '.' for localhost as it is more reliable in SSMS
    DB_CONNECTION = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=healthapp_db;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    # Add this line here
    SECRET_KEY = "udaya_bhavani"
