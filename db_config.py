import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",  # Replace with your MySQL password
        database="crm_db"
    )
    return connection