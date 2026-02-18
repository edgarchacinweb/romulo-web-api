from flask import Blueprint, jsonify, request, Response
from database.connection import Connection
from utils.Security import Security
from utils.image import resize, convert_to_webp
from models.Usuario import Rol
from utils.handler import exception_handler
from utils.helpers import number_to_letter
from utils.config import app
import os

student_bp = Blueprint("student", __name__)

def get_db():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    return conn, cursor

# --- FUNCIÓN AUXILIAR: ASIGNACIÓN INTELIGENTE DE SECCIÓN ---
def obtener_seccion_disponible(cursor, curso_id, periodo_id):
    """
    Busca la primera sección (1=A, 2=B...) que tenga menos de 30 estudiantes
    inscritos en el periodo actual.
    """
    CAPACIDAD_MAXIMA = 30
    
    # Probamos secciones de la 1 (A) a la 20 (T)
    for seccion_num in range(1, 21):
        # Contamos cuántos estudiantes hay en esta sección, curso y periodo
        query = """
            SELECT COUNT(*) 
            FROM "CursoEstudiante" 
            WHERE "CursoId" = %s 
            AND "Seccion" = %s 
            AND "PeriodoEscolarId" = %s
        """
        cursor.execute(query, (curso_id, seccion_num, periodo_id))
        cantidad = cursor.fetchone()[0]
        
        # Si hay espacio (menos de 30), retornamos esta sección
        if cantidad < CAPACIDAD_MAXIMA:
            print(f"Asignando Sección {number_to_letter(seccion_num)} ({cantidad}/{CAPACIDAD_MAXIMA} ocupados)")
            return seccion_num
            
    return 1 # Fallback: Si todo está lleno, asigna a la A (o podrías lanzar error)

# --- 1. VERIFICAR PERIODO ---
@student_bp.route("/students/check_period", methods=["GET"])
def check_period():
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoInscripcion" WHERE "Activo" = TRUE AND CURRENT_DATE BETWEEN "Inicio" AND "Fin" LIMIT 1;')
        row = cursor.fetchone()
        if row:
            return jsonify({"open": True, "periodoEscolarId": row[0]}), 200
        return jsonify({"open": False, "message": "Inscripción cerrada"}), 404
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 2. CREAR ESTUDIANTE (LOGICA MEJORADA) ---
@student_bp.route("/students/create", methods=["POST"])
def create():
    conn, cursor = get_db()
    try:
        if not Security.verify_token(request.headers): 
            return jsonify({"message": "No autorizado"}), 401

        data, files = request.form, request.files

        # 1. Crear Datos Persona
        cursor.execute("""INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Direccion") 
                           VALUES (%s,%s,%s,%s,%s) RETURNING "DatosPersonaId";""",
                        (data["Nombre"], data["Apellido"], data["Genero"], data["Cedula"], data["Direccion"]))
        dp_id = cursor.fetchone()[0]

        # 2. Crear Estudiante
        cursor.execute("""INSERT INTO "Estudiante" ("FechaNacimiento", "Parentesco", "DatosPersonaId", "RepresentanteId") 
                           VALUES (%s,%s,%s,%s) RETURNING "EstudianteId";""",
                        (data["FechaNacimiento"], data["Parentesco"], dp_id, data["IdRepresentante"]))
        est_id = cursor.fetchone()[0]

        # 3. Estado Inicial
        cursor.execute('INSERT INTO "EstadoEstudiante" ("EstudianteId", "Estado") VALUES (%s, \'revision\')', (est_id,))
        
        # --- ASIGNACIÓN DE SECCIÓN INTELIGENTE ---
        val_curso_id = str(data["IdCurso"]).strip()
        
        # A. Buscamos el periodo activo
        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoInscripcion" WHERE "Activo" = TRUE LIMIT 1;')
        periodo_row = cursor.fetchone()
        
        if not periodo_row:
            # Si no hay periodo activo, no podemos asignar sección correctamente
            raise Exception("No hay un periodo escolar activo para inscribir.")
        
        periodo_id = periodo_row[0]

        # B. Calculamos la sección disponible (A, B, C...) usando la función auxiliar
        seccion_asignada = obtener_seccion_disponible(cursor, val_curso_id, periodo_id)

        # C. Insertamos manualmente en CursoEstudiante con la sección calculada
        cursor.execute("""
            INSERT INTO "CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId")
            VALUES (%s, %s, %s, %s)
        """, (est_id, val_curso_id, seccion_asignada, periodo_id))
        # -----------------------------------------

        # 4. Guardar Archivos
        if "FotoCarnet" in files:
            path = os.path.join(app.config["UPLOAD_FOLDER"], f"carnet-{est_id}.webp")
            resize(convert_to_webp(files["FotoCarnet"])).save(path)
            
        docs_map = {"DocDni": "dni", "DocPartidaNacimiento": "partida", "DocNotasCertificadas": "notas"}
        for key, prefix in docs_map.items():
            if key in files:
                path = os.path.join(app.config["UPLOAD_FOLDER"], f"{prefix}-{est_id}.pdf")
                files[key].save(path)

        conn.commit()
        # Mostramos en el mensaje la sección asignada para confirmar
        return jsonify({"message": f"Estudiante registrado con éxito en la sección {number_to_letter(seccion_asignada)}"}), 201
    except Exception as err:
        conn.rollback()
        print(f"Error create: {err}")
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 3. OBTENER ESTUDIANTE (Edición) ---
@student_bp.route("/students/get/<string:id>", methods=["GET"])
def get_student(id):
    conn, cursor = get_db()
    try:
        query = """
            SELECT dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", dp."Direccion", 
                   e."FechaNacimiento", e."Parentesco", ce."CursoId"
            FROM "Estudiante" e
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            LEFT JOIN "CursoEstudiante" ce ON e."EstudianteId" = ce."EstudianteId"
            WHERE e."EstudianteId" = %s
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        if not row: return jsonify({"message": "No encontrado"}), 404

        return jsonify({
            "Nombre": row[0], "Apellido": row[1], "Genero": row[2], 
            "Cedula": row[3], "Direccion": row[4], "FechaNacimiento": str(row[5]), 
            "Parentesco": row[6], "IdCurso": row[7]
        }), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 4. FILTRAR SOLICITUDES (Admin) - CORREGIDO Y POTENCIADO ---
@student_bp.route("/students/filter", methods=["POST"])
def filter_students():
    conn, cursor = get_db()
    try:
        data = request.get_json() or {}
        
        # Recuperamos los filtros del Frontend
        estado = data.get("Estado", "revision")
        busqueda = data.get("Busqueda", "").strip()
        curso_id = data.get("CursoId", "")
        seccion = data.get("Seccion", "")

        # Consulta Base
        query = """
            SELECT e."EstudianteId", ee."Estado", dp."Nombre", dp."Apellido", dp."Cedula", 
                   c."Grado", ce."Seccion", e."FechaNacimiento",
                   rep."Nombre", rep."Apellido", u."UsuarioId", u."Email",
                   dp."Sexo", dp."Direccion",
                   e."Parentesco", rep."Cedula", rep."Telefono", rep."Ocupacion", rep."Direccion"
            FROM "Estudiante" e
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "EstadoEstudiante" ee ON e."EstudianteId" = ee."EstudianteId"
            JOIN "CursoEstudiante" ce ON e."EstudianteId" = ce."EstudianteId"
            JOIN "Curso" c ON ce."CursoId" = c."CursoId"
            JOIN "DatosPersona" rep ON e."RepresentanteId" = rep."DatosPersonaId"
            LEFT JOIN "Usuario" u ON rep."DatosPersonaId" = u."DatosPersona"
            WHERE ee."Estado" = %s
        """
        params = [estado]

        # --- APLICACIÓN DINÁMICA DE FILTROS ---
        
        # 1. Filtro por Grado (Curso)
        if curso_id and curso_id != "undefined" and curso_id != "":
            query += ' AND ce."CursoId" = %s'
            params.append(curso_id)

        # 2. Filtro por Sección
        if seccion and seccion != "undefined" and seccion != "":
            query += ' AND ce."Seccion" = %s'
            params.append(int(seccion))

        # 3. Filtro por Búsqueda (Nombre, Apellido o Cédula del Estudiante)
        if busqueda:
            query += """ AND (
                dp."Nombre" ILIKE %s OR 
                dp."Apellido" ILIKE %s OR 
                CAST(dp."Cedula" AS TEXT) ILIKE %s
            )"""
            search_term = f"%{busqueda}%"
            params.extend([search_term, search_term, search_term])

        # Ejecutamos la consulta con todos los parámetros acumulados
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        return jsonify([{
            "EstudianteId": r[0],
            "Estado": r[1],
            "FechaNacimiento": str(r[7]),
            "Parentesco": r[14],
            "DatosPersona": {
                "Nombre": r[2], "Apellido": r[3], "Cedula": r[4],
                "Sexo": r[12],      
                "Direccion": r[13]
            },
            "Curso": {
                "Grado": r[5], "Seccion": number_to_letter(r[6])
            },
            "Representante": {
                "Nombre": r[8], 
                "Apellido": r[9],
                "UsuarioId": r[10] if r[10] else "Sin Usuario", 
                "Email": r[11] if r[11] else "Sin Email",
                "Cedula": r[15],
                "Telefono": r[16],
                "Ocupacion": r[17],
                "Direccion": r[18]
            }
        } for r in rows]), 200
    except Exception as err:
        conn.rollback()
        print(f"Error filter: {err}")
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 5. APROBAR ESTUDIANTE ---
@student_bp.route("/students/approve/<string:id>", methods=["PUT"])
def approve_student(id):
    conn, cursor = get_db()
    try:
        # Cambiamos estado a 'inscrito'
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'inscrito\' WHERE "EstudianteId" = %s', (id,))
        # Activamos al estudiante
        cursor.execute('UPDATE "Estudiante" SET "Activo" = TRUE WHERE "EstudianteId" = %s', (id,))
        conn.commit()
        return jsonify({"message": "Estudiante aprobado exitosamente"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 6. RECHAZAR ESTUDIANTE ---
@student_bp.route("/students/reject/<string:id>", methods=["PUT"])
def reject_student(id):
    conn, cursor = get_db()
    try:
        # data = request.get_json() # Si quisieras guardar el motivo
        
        # Cambiamos estado a 'rechazado'
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'rechazado\' WHERE "EstudianteId" = %s', (id,))
        # Desactivamos temporalmente
        cursor.execute('UPDATE "Estudiante" SET "Activo" = FALSE WHERE "EstudianteId" = %s', (id,))
        conn.commit()
        return jsonify({"message": "Solicitud rechazada"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 7. CORREGIR SOLICITUD ---
@student_bp.route("/students/correct_application/<string:id>", methods=["PUT"])
def correct_application(id):
    conn, cursor = get_db()
    try:
        data = request.form
        cursor.execute('SELECT "DatosPersonaId" FROM "Estudiante" WHERE "EstudianteId" = %s', (id,))
        row = cursor.fetchone()
        if not row: raise Exception("Estudiante no encontrado")
        
        dp_id = row[0]
        cursor.execute('UPDATE "DatosPersona" SET "Nombre"=%s, "Apellido"=%s, "Cedula"=%s, "Direccion"=%s WHERE "DatosPersonaId"=%s',
                       (data["Nombre"], data["Apellido"], data["Cedula"], data["Direccion"], dp_id))
        
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'revision\' WHERE "EstudianteId" = %s', (id,))
        
        conn.commit()
        return jsonify({"message": "Solicitud enviada a revisión"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 8. OBTENER POR REPRESENTANTE ---
@student_bp.route("/students/by_parent/<string:parent_id>", methods=["GET"])
def get_all_by_parent(parent_id):
    conn, cursor = get_db()
    try:
        query = """
            SELECT DISTINCT ON (e."EstudianteId") 
                   e."EstudianteId", e."FechaNacimiento", c."Grado", ce."Seccion", 
                   dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", ee."Estado"
            FROM "Estudiante" e 
            JOIN "CursoEstudiante" ce ON ce."EstudianteId"=e."EstudianteId" 
            JOIN "Curso" c ON c."CursoId"=ce."CursoId" 
            JOIN "DatosPersona" dp ON e."DatosPersonaId"=dp."DatosPersonaId" 
            JOIN "EstadoEstudiante" ee ON ee."EstudianteId"=e."EstudianteId" 
            WHERE e."RepresentanteId"=%s 
            ORDER BY e."EstudianteId", c."Grado" DESC
        """
        cursor.execute(query, (parent_id,))
        rows = cursor.fetchall()
        
        return jsonify([
            {
                "EstudianteId": r[0], 
                "FechaNacimiento": str(r[1]),
                "Curso": {"Grado": r[2], "Seccion": number_to_letter(r[3])}, 
                "DatosPersona": {
                    "Nombre": r[4], 
                    "Apellido": r[5], 
                    "Sexo": r[6],
                    "Cedula": r[7]
                }, 
                "EstadoEstudiante": {"Estado": r[8]}
            } for r in rows
        ]), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 9. CONTAR ---
@student_bp.route("/students/count/by_parent/<string:parent_id>", methods=["GET"])
def count_by_parent(parent_id):
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT COUNT(*) FROM "Estudiante" WHERE "RepresentanteId" = %s', (parent_id,))
        row = cursor.fetchone()
        return jsonify({"count": row[0] if row else 0}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 10. CAMBIAR ESTADO (Admin) ---
@student_bp.route("/students/change_status/<string:id>", methods=["PUT"])
def change_status(id):
    conn, cursor = get_db()
    try:
        data = request.get_json()
        new_status = data.get("Estado")
        
        # Validar el estado
        valid_statuses = ["inscrito", "retirado", "graduado", "revision", "rechazado"]
        if new_status not in valid_statuses:
             return jsonify({"message": "Estado no válido"}), 400

        # Actualizar tabla EstadoEstudiante
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = %s WHERE "EstudianteId" = %s', (new_status, id))
        
        # Actualizar Activo en tabla Estudiante
        is_active = True if new_status in ["inscrito", "revision"] else False
        cursor.execute('UPDATE "Estudiante" SET "Activo" = %s WHERE "EstudianteId" = %s', (is_active, id))

        conn.commit()
        return jsonify({"message": f"Estado actualizado a {new_status}"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()