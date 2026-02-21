from flask import Blueprint, jsonify, request, Response
from database.connection import Connection
from utils.Security import Security
from utils.image import resize, convert_to_webp
from models.Usuario import Rol
from utils.handler import exception_handler
from utils.helpers import number_to_letter
from utils.email import send_email
from utils.config import app
import os
import re
from datetime import datetime

student_bp = Blueprint("student", __name__)

def get_db():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    return conn, cursor

# --- FUNCIÓN AUXILIAR: VALIDACIÓN DE SOLO LETRAS ---
def validar_solo_letras(texto, campo):
    if not texto or not texto.strip():
        raise Exception(f"El campo {campo} es requerido.")
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", texto.strip()):
        raise Exception(f"El campo {campo} solo debe contener letras.")

# --- FUNCIÓN AUXILIAR: VALIDACIÓN ESTRICTA DE CÉDULA DE ESTUDIANTE ---
def validar_cedula_estudiante(cedula_str):
    cedula_limpia = str(cedula_str).replace("-", "").strip().upper()
    if len(cedula_limpia) <= 9:
        is_extranjero = cedula_limpia.startswith("E")
        solo_numeros = ''.join(filter(str.isdigit, cedula_limpia))
        if solo_numeros:
            num = int(solo_numeros)
            if num < 33000000: raise Exception("El número de Cédula de Identidad del estudiante debe ser mayor a 33.000.000")
            if not is_extranjero and num > 40000000: raise Exception("El número de Cédula de Identidad para Venezolanos (V) no debe exceder los 40.000.000")
            if is_extranjero and num > 90000000: raise Exception("El número de Cédula de Identidad para Extranjeros (E) no debe exceder los 90.000.000")

# --- FUNCIÓN AUXILIAR: VALIDACIÓN DE FECHA DE NACIMIENTO ---
def validar_fecha_nacimiento(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        if fecha.year < 2008 or fecha.year > 2015:
            raise Exception("El año de nacimiento del estudiante debe estar estrictamente entre 2008 y 2015.")
    except ValueError:
        raise Exception("Formato de fecha de nacimiento inválido.")

# --- FUNCIÓN AUXILIAR: ASIGNACIÓN INTELIGENTE DE SECCIÓN ---
def obtener_seccion_disponible(cursor, curso_id, periodo_id):
    CAPACIDAD_MAXIMA = 30
    for seccion_num in range(1, 21):
        query = """
            SELECT COUNT(*) 
            FROM "CursoEstudiante" 
            WHERE "CursoId" = %s 
            AND "Seccion" = %s 
            AND "PeriodoEscolarId" = %s
        """
        cursor.execute(query, (curso_id, seccion_num, periodo_id))
        cantidad = cursor.fetchone()[0]
        if cantidad < CAPACIDAD_MAXIMA:
            return seccion_num
    return 1

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

# --- 2. CREAR ESTUDIANTE ---
@student_bp.route("/students/create", methods=["POST"])
def create():
    conn, cursor = get_db()
    try:
        if not Security.verify_token(request.headers): 
            return jsonify({"message": "No autorizado"}), 401

        data, files = request.form, request.files
        
        if "Nombre" in data: validar_solo_letras(data["Nombre"], "Nombre")
        if "Apellido" in data: validar_solo_letras(data["Apellido"], "Apellido")
        if "Cedula" in data: validar_cedula_estudiante(data["Cedula"])

        if "FechaNacimiento" in data:
            validar_fecha_nacimiento(data["FechaNacimiento"])
        else:
            raise Exception("La fecha de nacimiento es requerida.")

        cursor.execute("""INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Direccion") 
                           VALUES (%s,%s,%s,%s,%s) RETURNING "DatosPersonaId";""",
                        (data["Nombre"].strip(), data["Apellido"].strip(), data["Genero"], data["Cedula"], data["Direccion"]))
        dp_id = cursor.fetchone()[0]

        cursor.execute("""INSERT INTO "Estudiante" ("FechaNacimiento", "Parentesco", "DatosPersonaId", "RepresentanteId") 
                           VALUES (%s,%s,%s,%s) RETURNING "EstudianteId";""",
                        (data["FechaNacimiento"], data["Parentesco"], dp_id, data["IdRepresentante"]))
        est_id = cursor.fetchone()[0]

        cursor.execute('INSERT INTO "EstadoEstudiante" ("EstudianteId", "Estado") VALUES (%s, \'revision\')', (est_id,))
        
        val_curso_id = str(data["IdCurso"]).strip()
        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoInscripcion" WHERE "Activo" = TRUE LIMIT 1;')
        periodo_row = cursor.fetchone()
        if not periodo_row: raise Exception("No hay un periodo escolar activo para inscribir.")
        periodo_id = periodo_row[0]
        seccion_asignada = obtener_seccion_disponible(cursor, val_curso_id, periodo_id)

        cursor.execute("""
            INSERT INTO "CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId")
            VALUES (%s, %s, %s, %s)
        """, (est_id, val_curso_id, seccion_asignada, periodo_id))

        if "FotoCarnet" in files:
            path = os.path.join(app.config["UPLOAD_FOLDER"], f"carnet-{est_id}.webp")
            resize(convert_to_webp(files["FotoCarnet"])).save(path)
            
        docs_map = {
            "DocDni": "dni", "DocCedula": "dni", "DocCI": "dni", 
            "DocPartidaNacimiento": "partida", "DocNotasCertificadas": "notas", "DocAutorizacion": "autorizacion"
        }
        
        for key, prefix in docs_map.items():
            if key in files:
                path = os.path.join(app.config["UPLOAD_FOLDER"], f"{prefix}-{est_id}.pdf")
                files[key].save(path)

        conn.commit()
        return jsonify({"message": f"Estudiante registrado con éxito en la sección {number_to_letter(seccion_asignada)}"}), 201
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 3. OBTENER ESTUDIANTE ---
@student_bp.route("/students/get/<string:id>", methods=["GET"])
def get_student(id):
    conn, cursor = get_db()
    try:
        # AQUÍ ESTÁ EL CAMBIO: Se agregó c."Grado" al SELECT para poder sumarle un año en el frontend
        query = """
            SELECT dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", dp."Direccion", 
                   e."FechaNacimiento", e."Parentesco", ce."CursoId", c."Grado"
            FROM "Estudiante" e
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            LEFT JOIN "CursoEstudiante" ce ON e."EstudianteId" = ce."EstudianteId"
            LEFT JOIN "Curso" c ON ce."CursoId" = c."CursoId"
            WHERE e."EstudianteId" = %s
            ORDER BY c."Grado" DESC NULLS LAST
            LIMIT 1
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        if not row: return jsonify({"message": "No encontrado"}), 404

        return jsonify({
            "Nombre": row[0], "Apellido": row[1], "Genero": row[2], 
            "Cedula": row[3], "Direccion": row[4], "FechaNacimiento": str(row[5]), 
            "Parentesco": row[6], "IdCurso": row[7], "Grado": row[8]
        }), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 4. FILTRAR SOLICITUDES ---
@student_bp.route("/students/filter", methods=["POST"])
def filter_students():
    conn, cursor = get_db()
    try:
        data = request.get_json() or {}
        
        estado = data.get("Estado", "revision")
        busqueda = data.get("Busqueda", "").strip()
        curso_id = data.get("CursoId", "")
        seccion = data.get("Seccion", "")

        query = """
            SELECT DISTINCT ON (e."EstudianteId") 
                   e."EstudianteId", ee."Estado", dp."Nombre", dp."Apellido", dp."Cedula", 
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

        if curso_id and curso_id != "undefined" and curso_id != "":
            query += ' AND ce."CursoId" = %s'
            params.append(curso_id)

        if seccion and seccion != "undefined" and seccion != "":
            query += ' AND ce."Seccion" = %s'
            params.append(int(seccion))

        if busqueda:
            query += """ AND (
                dp."Nombre" ILIKE %s OR 
                dp."Apellido" ILIKE %s OR 
                CAST(dp."Cedula" AS TEXT) ILIKE %s
            )"""
            search_term = f"%{busqueda}%"
            params.extend([search_term, search_term, search_term])

        query += ' ORDER BY e."EstudianteId", c."Grado" DESC'

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        return jsonify([{
            "EstudianteId": r[0], "Estado": r[1], "FechaNacimiento": str(r[7]), "Parentesco": r[14],
            "DatosPersona": { "Nombre": r[2], "Apellido": r[3], "Cedula": r[4], "Sexo": r[12], "Direccion": r[13] },
            "Curso": { "Grado": r[5], "Seccion": number_to_letter(r[6]) },
            "Representante": {
                "Nombre": r[8], "Apellido": r[9], "UsuarioId": r[10] if r[10] else "Sin Usuario", 
                "Email": r[11] if r[11] else "Sin Email", "Cedula": r[15], "Telefono": r[16],
                "Ocupacion": r[17], "Direccion": r[18]
            }
        } for r in rows]), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- 5. APROBAR ESTUDIANTE ---
@student_bp.route("/students/approve/<string:id>", methods=["PUT"])
def approve_student(id):
    conn, cursor = get_db()
    try:
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'inscrito\' WHERE "EstudianteId" = %s', (id,))
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
        data = request.get_json()
        email, motivo, descripcion = data.get("Email"), data.get("Motivo"), data.get("Descripcion")

        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'rechazado\' WHERE "EstudianteId" = %s', (id,))
        cursor.execute('UPDATE "Estudiante" SET "Activo" = FALSE WHERE "EstudianteId" = %s', (id,))
        conn.commit()

        status_email = "Correo no enviado"
        if email and "@" in email and "Sin Email" not in email:
            subject = " Solicitud de Inscripción Rechazada - Liceo Nacional Don Rómulo Gallegos"
            text_body = f"Motivo: {motivo}\nDetalles: {descripcion}"
            html_body = f"<p>Motivo: {motivo}</p><p>Detalles: {descripcion}</p>"
            try:
                send_email(email, subject, text_body, html_body)
                status_email = "Notificación enviada por correo"
            except Exception as e:
                status_email = f"Error enviando correo: {str(e)}"

        return jsonify({"message": f"Solicitud rechazada. {status_email}"}), 200
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
        
        if "Nombre" in data: validar_solo_letras(data["Nombre"], "Nombre")
        if "Apellido" in data: validar_solo_letras(data["Apellido"], "Apellido")
        if "Cedula" in data: validar_cedula_estudiante(data["Cedula"])
            
        cursor.execute('SELECT "DatosPersonaId" FROM "Estudiante" WHERE "EstudianteId" = %s', (id,))
        row = cursor.fetchone()
        if not row: raise Exception("Estudiante no encontrado")
        
        dp_id = row[0]
        cursor.execute('UPDATE "DatosPersona" SET "Nombre"=%s, "Apellido"=%s, "Cedula"=%s, "Direccion"=%s WHERE "DatosPersonaId"=%s',
                       (data["Nombre"].strip(), data["Apellido"].strip(), data["Cedula"], data["Direccion"], dp_id))
        
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'revision\' WHERE "EstudianteId" = %s', (id,))
        
        conn.commit()
        return jsonify({"message": "Solicitud enviada a revisión"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()

# --- NUEVO: 7.1 ENVIAR REINSCRIPCIÓN ---
@student_bp.route("/students/submit_reinscription/<string:id>", methods=["PUT"])
def submit_reinscription(id):
    conn, cursor = get_db()
    try:
        data, files = request.form, request.files

        # Validaciones de Seguridad
        if "Nombre" in data: validar_solo_letras(data["Nombre"], "Nombre")
        if "Apellido" in data: validar_solo_letras(data["Apellido"], "Apellido")
        if "Cedula" in data: validar_cedula_estudiante(data["Cedula"])
        if "FechaNacimiento" in data: validar_fecha_nacimiento(data["FechaNacimiento"])

        # 1. Actualizar DatosPersona (Por si el representante corrigió el nombre o dirección)
        cursor.execute('SELECT "DatosPersonaId" FROM "Estudiante" WHERE "EstudianteId" = %s', (id,))
        row = cursor.fetchone()
        if not row: raise Exception("Estudiante no encontrado")
        dp_id = row[0]
        
        cursor.execute('UPDATE "DatosPersona" SET "Nombre"=%s, "Apellido"=%s, "Cedula"=%s, "Direccion"=%s WHERE "DatosPersonaId"=%s',
                       (data["Nombre"].strip(), data["Apellido"].strip(), data["Cedula"], data["Direccion"], dp_id))
        
        # 2. Devolver Estado a Revisión
        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = \'revision\' WHERE "EstudianteId" = %s', (id,))

        # 3. Asignación del nuevo Curso / Año escolar activo
        val_curso_id = str(data["IdCurso"]).strip()
        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoInscripcion" WHERE "Activo" = TRUE LIMIT 1;')
        periodo_row = cursor.fetchone()
        if not periodo_row: raise Exception("No hay un periodo de inscripción activo para reinscribir.")
        periodo_id = periodo_row[0]

        # Validar que no se generen registros duplicados si fue rechazado e intenta otra vez la reinscripción en el mismo periodo
        cursor.execute('SELECT * FROM "CursoEstudiante" WHERE "EstudianteId" = %s AND "PeriodoEscolarId" = %s', (id, periodo_id))
        if cursor.fetchone():
            cursor.execute('UPDATE "CursoEstudiante" SET "CursoId" = %s WHERE "EstudianteId" = %s AND "PeriodoEscolarId" = %s', (val_curso_id, id, periodo_id))
        else:
            seccion_asignada = obtener_seccion_disponible(cursor, val_curso_id, periodo_id)
            cursor.execute("""
                INSERT INTO "CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId")
                VALUES (%s, %s, %s, %s)
            """, (id, val_curso_id, seccion_asignada, periodo_id))

        # 4. Procesar SOLO los archivos nuevos (Si suben algo nuevo se sobreescribe, si no, se conservan los anteriores)
        if "FotoCarnet" in files:
            path = os.path.join(app.config["UPLOAD_FOLDER"], f"carnet-{id}.webp")
            resize(convert_to_webp(files["FotoCarnet"])).save(path)
            
        docs_map = {
            "DocDni": "dni", "DocPartidaNacimiento": "partida", 
            "DocNotasCertificadas": "notas", "DocAutorizacion": "autorizacion"
        }
        for key, prefix in docs_map.items():
            if key in files:
                path = os.path.join(app.config["UPLOAD_FOLDER"], f"{prefix}-{id}.pdf")
                files[key].save(path)

        conn.commit()
        return jsonify({"message": "Solicitud de reinscripción enviada a revisión con éxito."}), 200
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
                   dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", ee."Estado", ce."PeriodoEscolarId"
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
                "Curso": {"Grado": r[2], "Seccion": number_to_letter(r[3]), "PeriodoEscolarId": r[9]}, 
                "DatosPersona": {
                    "Nombre": r[4], "Apellido": r[5], "Sexo": r[6], "Cedula": r[7]
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
        
        valid_statuses = ["inscrito", "retirado", "graduado", "revision", "rechazado"]
        if new_status not in valid_statuses:
             return jsonify({"message": "Estado no válido"}), 400

        cursor.execute('UPDATE "EstadoEstudiante" SET "Estado" = %s WHERE "EstudianteId" = %s', (new_status, id))
        
        is_active = True if new_status in ["inscrito", "revision"] else False
        cursor.execute('UPDATE "Estudiante" SET "Activo" = %s WHERE "EstudianteId" = %s', (is_active, id))

        conn.commit()
        return jsonify({"message": f"Estado actualizado a {new_status}"}), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"message": str(err)}), 500
    finally:
        cursor.close()