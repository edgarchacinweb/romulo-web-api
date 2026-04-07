import sys
import os
sys.path.append(os.getcwd())
try:
    from database.connection import Connection
    conn = Connection().get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "DocenteMateria" LIMIT 5;')
    print('DocenteMateria:', cursor.fetchall())
    cursor.execute('SELECT * FROM "MateriaHorasAcademicas" LIMIT 5;')
    print('MateriaHorasAcademicas:', cursor.fetchall())
    cursor.execute('SELECT * FROM "Curso" LIMIT 5;')
    print('Curso:', cursor.fetchall())
    cursor.execute('SELECT * FROM "Clase" LIMIT 5;')
    print('Clase:', cursor.fetchall())
except Exception as e:
    print(f"Error: {e}")
