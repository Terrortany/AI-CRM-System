from db_config import get_connection

try:
    conn = get_connection()
    print("✅ Database connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")