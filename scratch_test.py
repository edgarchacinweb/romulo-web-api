from database.connection import Connection
import json

conn = Connection().get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM \"Horario\" LIMIT 5;")
    print("Horario:", cursor.fetchall())
    
    cursor.execute("SELECT \"PeriodoEscolarId\", \"Activo\" FROM \"PeriodoEscolar\" ORDER BY \"FechaInicio\" DESC LIMIT 2;")
    print("PeriodoEscolar:", cursor.fetchall())
except Exception as e:
    print(e)
finally:
    cursor.close()
