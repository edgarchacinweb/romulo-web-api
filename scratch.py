import database.connection as c
conn = c.Connection().get_connection()
cur = conn.cursor()
cur.execute('SELECT "MateriaId", "Nombre" FROM "Materia"')
materias = cur.fetchall()
print("Todas las materias:")
for m in materias:
    print(m)

cur.execute('''
    SELECT h."HorarioId", h."CursoId", h."Seccion", m."Nombre" 
    FROM "Horario" h 
    JOIN "Materia" m ON h."MateriaId" = m."MateriaId"
    WHERE m."Nombre" LIKE '%FISICA%' OR m."Nombre" LIKE '%CREACIÓN%'
''')
horarios = cur.fetchall()
print("\nHorarios con Física o Creación:")
for h in horarios:
    print(h)
