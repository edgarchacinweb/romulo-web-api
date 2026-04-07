import sys
import os
sys.path.append('c:\\Users\\pc\\Documents\\proyecto\\romulo-web-api')
from database.connection import Connection

conn = Connection().get_connection()
cursor = conn.cursor()
cursor.execute('SELECT "PeriodoEscolarId", "FechaInicio", "FechaFin", "Activo" FROM "PeriodoEscolar"')
rows = cursor.fetchall()
for row in rows:
    print(row)
