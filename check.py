import sys
import os
sys.path.append(os.getcwd())
try:
    from database.connection import Connection
    conn = Connection().get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'DocenteMateria';")
    print('DocenteMateria schema:', cursor.fetchall())
except Exception as e:
    print(f"Error: {e}")
