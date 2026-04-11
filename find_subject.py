from database.connection import Connection
import json

def get_subject():
    try:
        conn = Connection().get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT \"MateriaId\", \"Nombre\" FROM \"Materia\" WHERE \"Nombre\" ILIKE '%ORIENTACION%'")
        rows = cursor.fetchall()
        print(json.dumps([{"id": r[0], "name": r[1]} for r in rows]))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    get_subject()
