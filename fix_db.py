import database.connection as c

def fix_db():
    conn = c.Connection().get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Identificar las IDs
        cursor.execute("SELECT \"MateriaId\" FROM \"Materia\" WHERE \"Nombre\" = 'EDUCACIÓN FISICA';")
        row = cursor.fetchone()
        id_sin_tilde = row[0] if row else None
        
        cursor.execute("SELECT \"MateriaId\" FROM \"Materia\" WHERE \"Nombre\" = 'EDUCACIÓN FÍSICA';")
        row = cursor.fetchone()
        id_con_tilde = row[0] if row else None
        
        if id_sin_tilde and id_con_tilde:
            print(f"Encontradas ambas materias.\nSin tilde: {id_sin_tilde}\nCon tilde: {id_con_tilde}")
            
            # Migrar Notas
            cursor.execute("""
                UPDATE "Nota" SET "MateriaId" = %s WHERE "MateriaId" = %s;
            """, (id_con_tilde, id_sin_tilde))
            
            # Migrar MateriaHorasAcademicas
            cursor.execute("""
                UPDATE "MateriaHorasAcademicas" mha1
                SET "MateriaId" = %s
                WHERE "MateriaId" = %s
                AND NOT EXISTS (
                    SELECT 1 FROM "MateriaHorasAcademicas" mha2 
                    WHERE mha2."MateriaId" = %s AND mha2."CursoId" = mha1."CursoId"
                );
            """, (id_con_tilde, id_sin_tilde, id_con_tilde))
            cursor.execute('DELETE FROM "MateriaHorasAcademicas" WHERE "MateriaId" = %s;', (id_sin_tilde,))
            
            # Migrar Horario
            cursor.execute("""
                UPDATE "Horario" SET "MateriaId" = %s WHERE "MateriaId" = %s;
            """, (id_con_tilde, id_sin_tilde))
            
            # Migrar DocenteMateria
            cursor.execute("""
                UPDATE "DocenteMateria" dm1
                SET "MateriaId" = %s
                WHERE "MateriaId" = %s
                AND NOT EXISTS (
                    SELECT 1 FROM "DocenteMateria" dm2 
                    WHERE dm2."MateriaId" = %s AND dm2."DocenteId" = dm1."DocenteId"
                );
            """, (id_con_tilde, id_sin_tilde, id_con_tilde))
            cursor.execute('DELETE FROM "DocenteMateria" WHERE "MateriaId" = %s;', (id_sin_tilde,))
            
            # Migrar Clase
            cursor.execute("""
                UPDATE "Clase" SET "MateriaId" = %s WHERE "MateriaId" = %s;
            """, (id_con_tilde, id_sin_tilde))
            
            # Borrar la materia fantasma
            cursor.execute('DELETE FROM "Materia" WHERE "MateriaId" = %s;', (id_sin_tilde,))
            
            conn.commit()
            print("Limpieza completada con exito.")
        else:
            print("No se encontraron ambas materias o ya se realizo la limpieza.")
            
        # También limpiar "GRUPO DE CREACIÓN" si no debería estar en el Horario o no tiene horas académicas.
        # ¿"GRUPO DE CREACIÓN" es una materia real? 
        cursor.execute("SELECT \"MateriaId\" FROM \"Materia\" WHERE \"Nombre\" = 'GRUPO DE CREACIÓN';")
        grupo = cursor.fetchone()
        if grupo:
            print(f"'GRUPO DE CREACIÓN' está en la base de datos con ID {grupo[0]}")
            
    except Exception as e:
        conn.rollback()
        print("Error:", str(e))
    finally:
        cursor.close()

if __name__ == '__main__':
    fix_db()
