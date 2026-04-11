import psycopg2
from database.connection import Connection

def check_duplicates():
    try:
        conn = Connection().get_connection()
        cursor = conn.cursor()
        
        print("Checking duplicate subjects in MateriaHorasAcademicas per CursoId:")
        cursor.execute('''
            SELECT "CursoId", "MateriaId", COUNT(*)
            FROM "MateriaHorasAcademicas"
            GROUP BY "CursoId", "MateriaId"
            HAVING COUNT(*) > 1;
        ''')
        rows = cursor.fetchall()
        for r in rows:
            print(f"CursoId: {r[0]}, MateriaId: {r[1]}, Count: {r[2]}")
            
        print("\nChecking subjects with same name but different IDs:")
        cursor.execute('''
            SELECT "Nombre", COUNT(*)
            FROM "Materia"
            GROUP BY "Nombre"
            HAVING COUNT(*) > 1;
        ''')
        rows = cursor.fetchall()
        for r in rows:
            print(f"Nombre: {r[0]}, Count: {r[1]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicates()
