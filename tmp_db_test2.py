import sys
import os
sys.path.append(os.getcwd())
try:
    from database.connection import Connection
    conn = Connection().get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "Auditoria" AS a INNER JOIN "Usuario" AS u ON a."UsuarioId" = u."UsuarioId" LIMIT 1;')
    row = cursor.fetchone()
    print("Columns in select *:")
    if row:
        for i, description in enumerate(cursor.description):
            print(f"{i}: {description.name} - {type(row[i])} - {row[i]}")
    
    # test fetch all
    from database.Auditoria import AuditoriaRep
    from models.Auditoria import Auditoria
    
    rep = AuditoriaRep()
    res = rep.filter(Auditoria({}), None, None)
    print("Filter length:", len(res))
    
except Exception as e:
    import traceback
    traceback.print_exc()
