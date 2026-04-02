from flask import Blueprint, jsonify, request, Response, send_file
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
import math
from datetime import datetime
import io
import traceback

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

# --- FUNCIONES DE ASIGNACIÓN DINÁMICA DE SECCIÓN ---
def calcular_distribucion_secciones(total_estudiantes):
    min_estud = 15
    max_estud = 30
    max_secciones = 3
    if total_estudiantes == 0:
        return {}
    
    secciones = math.ceil(total_estudiantes / max_estud)
    if secciones == 0:
        secciones = 1
    if secciones > max_secciones:
        secciones = max_secciones

    base = total_estudiantes // secciones
    sobrantes = total_estudiantes % secciones

    distribucion = {}
    for i in range(1, secciones + 1):
        cupos = base + (1 if i <= sobrantes else 0)
        distribucion[i] = cupos

    res = {1: 0, 2: 0, 3: 0}
    for k, v in distribucion.items():
        res[k] = v
        
    return res

def balancear_secciones_curso(cursor, curso_id, periodo_id):
    query_est = """
        SELECT ce."EstudianteId"
        FROM "CursoEstudiante" ce
        JOIN "EstadoEstudiante" ee ON ce."EstudianteId" = ee."EstudianteId"
        WHERE ce."CursoId" = %s AND ce."PeriodoEscolarId" = %s
        AND ee."Estado" = 'inscrito'
        ORDER BY ce."EstudianteId" ASC
    """
    cursor.execute(query_est, (curso_id, periodo_id))
    estudiantes = cursor.fetchall()
    total = len(estudiantes)

    if total == 0:
        return

    dist = calcular_distribucion_secciones(total)
    
    secciones_asignar = []
    for seccion, cantidad in dist.items():
        secciones_asignar.extend([seccion] * cantidad)

    for index, est in enumerate(estudiantes):
        seccion_nueva = secciones_asignar[index] if index < len(secciones_asignar) else 3
        est_id = est[0]
        cursor.execute('''UPDATE "CursoEstudiante" SET "Seccion" = %s WHERE "EstudianteId" = %s AND "CursoId" = %s AND "PeriodoEscolarId" = %s''',
                       (seccion_nueva, est_id, curso_id, periodo_id))

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
        payload = Security.verify_token(request.headers)
        if not payload: 
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
        
        is_admin = payload.get("role") == Rol.ADMIN.name
        if not periodo_row and is_admin:
            cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoEscolar" ORDER BY "PeriodoEscolarId" DESC LIMIT 1;')
            periodo_row = cursor.fetchone()
            
        if not periodo_row: raise Exception("No hay un periodo escolar activo para inscribir.")
        periodo_id = periodo_row[0]
        seccion_asignada = 0

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
        return jsonify({"message": "Estudiante registrado con éxito en estado revisión. Sección: Por asignar"}), 201
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
        query = """
            SELECT dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", dp."Direccion", 
                   e."FechaNacimiento", e."Parentesco", ce."CursoId", c."Grado", ce."Seccion"
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
            "Parentesco": row[6], "IdCurso": row[7], "Grado": row[8],
            "Seccion": "Por asignar" if row[9] == 0 or row[9] is None else number_to_letter(row[9])
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
        periodo_escolar_id = data.get("PeriodoEscolarId", "")

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

        if periodo_escolar_id and periodo_escolar_id != "undefined" and periodo_escolar_id != "":
            query += ' AND ce."PeriodoEscolarId" = %s'
            params.append(periodo_escolar_id)

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
            "Curso": { "Grado": r[5], "Seccion": "Por asignar" if r[6] == 0 else number_to_letter(r[6]) },
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
        
        cursor.execute('SELECT "CursoId", "PeriodoEscolarId" FROM "CursoEstudiante" WHERE "EstudianteId" = %s ORDER BY "PeriodoEscolarId" DESC LIMIT 1', (id,))
        curso_info = cursor.fetchone()
        if curso_info:
            balancear_secciones_curso(cursor, curso_info[0], curso_info[1])
            
        conn.commit()
        return jsonify({"message": "Estudiante aprobado exitosamente y secciones balanceadas"}), 200
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

        # 1. Actualizar DatosPersona
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

        cursor.execute('SELECT * FROM "CursoEstudiante" WHERE "EstudianteId" = %s AND "PeriodoEscolarId" = %s', (id, periodo_id))
        if cursor.fetchone():
            cursor.execute('UPDATE "CursoEstudiante" SET "CursoId" = %s, "Seccion" = 0 WHERE "EstudianteId" = %s AND "PeriodoEscolarId" = %s', (val_curso_id, id, periodo_id))
        else:
            seccion_asignada = 0
            cursor.execute("""
                INSERT INTO "CursoEstudiante" ("EstudianteId", "CursoId", "Seccion", "PeriodoEscolarId")
                VALUES (%s, %s, %s, %s)
            """, (id, val_curso_id, seccion_asignada, periodo_id))

        # 4. Procesar SOLO los archivos nuevos
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
                "Curso": {"Grado": r[2], "Seccion": "Por asignar" if r[3] == 0 else number_to_letter(r[3]), "PeriodoEscolarId": r[9]}, 
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

# --- 11. DESCARGAR PLANILLA DE INSCRIPCIÓN ---
@student_bp.route("/students/enrollment_form/<string:id>", methods=["GET"])
def download_enrollment_form(id):
    conn, cursor = get_db()
    try:
        # 1. Obtener datos completos y hacer JOIN con PeriodoEscolar
        query = """
            SELECT dp."Nombre", dp."Apellido", dp."Cedula", dp."Sexo", dp."Direccion",
                   e."FechaNacimiento", e."Parentesco",
                   c."Grado", ce."Seccion",
                   rep."Nombre", rep."Apellido", rep."Cedula", rep."Telefono", u."Email", rep."Ocupacion",
                   pe."FechaInicio", pe."FechaFin"
            FROM "Estudiante" e
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            LEFT JOIN "CursoEstudiante" ce ON e."EstudianteId" = ce."EstudianteId"
            LEFT JOIN "Curso" c ON ce."CursoId" = c."CursoId"
            JOIN "DatosPersona" rep ON e."RepresentanteId" = rep."DatosPersonaId"
            LEFT JOIN "Usuario" u ON rep."DatosPersonaId" = u."DatosPersona"
            LEFT JOIN "PeriodoEscolar" pe ON ce."PeriodoEscolarId" = pe."PeriodoEscolarId"
            WHERE e."EstudianteId" = %s
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"message": "Estudiante no encontrado"}), 404

        # --- RECOPILACIÓN DE FECHAS (IMPRESIÓN Y PERIODO ESCOLAR) ---
        # Fecha de hoy (con formato AM/PM garantizado)
        fecha_impresion = datetime.now().strftime("%d/%m/%Y %I:%M %p").upper()
        
        # Formatear el periodo escolar sacando solo los años (Ej: 2024 - 2025)
        periodo_str = "No asignado"
        if row[15] and row[16]:
            try:
                year_start = str(row[15]).split('-')[0]
                year_end = str(row[16]).split('-')[0]
                periodo_str = f"{year_start} - {year_end}"
            except Exception:
                pass


        # 2. Intentar generar PDF usando ReportLab
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            return jsonify({"message": "Falta la librería PDF en el servidor. Ejecute: pip install reportlab"}), 500

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # --- DIBUJAR MEMBRETE Y LOGO ---
        
        # LOGO DIRECTO DESDE EL BACKEND:
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'romulo.png')
        
        if os.path.exists(logo_path):
            try:
                p.drawImage(logo_path, 40, height - 100, width=70, height=70, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Error cargando logo desde {logo_path}: {e}")
        else:
            print(f"\n⚠️ ADVERTENCIA: No se encontró el logo en {logo_path}.\n")

        # Texto del Membrete (Centrado)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(width / 2.0, height - 40, "REPÚBLICA BOLIVARIANA DE VENEZUELA")
        p.drawCentredString(width / 2.0, height - 52, "MINISTERIO DEL PODER POPULAR PARA LA EDUCACIÓN")
        p.drawCentredString(width / 2.0, height - 64, "LICEO NACIONAL DON ROMULO GALLEGOS * S2990D0503")
        
        p.setFont("Helvetica", 8)
        p.drawCentredString(width / 2.0, height - 76, "C/SAN MATEO, BARRIO ALAYON, P. ANDRES ELOY BLANCO MARACAY")

      

        # --- NUEVOS CAMPOS: PERIODO Y FECHA DE IMPRESIÓN (Justo debajo del membrete) ---
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, height - 125, f"Período Escolar: {periodo_str}")
        p.drawRightString(550, height - 125, f"Fecha de Emisión: {fecha_impresion}")

        # --- TÍTULO DE LA PLANILLA ---
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2.0, height - 160, "PLANILLA DE INSCRIPCIÓN")

        # --- DATOS DEL ESTUDIANTE ---
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 200, "DATOS DEL ESTUDIANTE")
        p.line(50, height - 205, 550, height - 205)

        p.setFont("Helvetica", 10)
        p.drawString(50, height - 225, f"Nombres y Apellidos: {row[0]} {row[1]}")
        p.drawString(350, height - 225, f"Cédula: {row[2]}")
        p.drawString(50, height - 245, f"Fecha de Nacimiento: {row[5]}")
        p.drawString(350, height - 245, f"Género: {row[3]}")
        p.drawString(50, height - 265, f"Dirección: {row[4]}")
        
        grado_str = f"{row[7]}° Año" if row[7] else "No asignado"
        p.drawString(50, height - 285, f"Grado a cursar: {grado_str}")
        
        seccion_str = number_to_letter(row[8]) if row[8] else "N/A"
        p.drawString(350, height - 285, f"Sección: {seccion_str}")

        # --- DATOS DEL REPRESENTANTE ---
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 330, "DATOS DEL REPRESENTANTE")
        p.line(50, height - 335, 550, height - 335)

        p.setFont("Helvetica", 10)
        p.drawString(50, height - 355, f"Nombres y Apellidos: {row[9]} {row[10]}")
        p.drawString(350, height - 355, f"Cédula: {row[11]}")
        p.drawString(50, height - 375, f"Parentesco: {row[6]}")
        p.drawString(350, height - 375, f"Teléfono: {row[12] if row[12] else 'No registrado'}")
        p.drawString(50, height - 395, f"Email: {row[13] if row[13] else 'No registrado'}")
        p.drawString(350, height - 395, f"Ocupación: {row[14] if row[14] else 'No registrado'}")

        # Pie de página
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, 50, "Documento generado automáticamente por el Sistema de Inscripción Estudiantil.")

        p.showPage()
        p.save()

        buffer.seek(0)
        
        # Bloque Try para compatibilidad con distintas versiones de Flask
        try:
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"Planilla_Inscripcion_{row[0]}_{row[1]}.pdf",
                mimetype="application/pdf"
            )
        except TypeError:
            # Compatibilidad con versiones más antiguas de Flask
            return send_file(
                buffer,
                as_attachment=True,
                attachment_filename=f"Planilla_Inscripcion_{row[0]}_{row[1]}.pdf",
                mimetype="application/pdf"
            )

    except Exception as err:
        conn.rollback()
        # IMPRESIÓN DEL ERROR EXACTO EN LA TERMINAL PARA DIAGNÓSTICO
        print("\n" + "="*40)
        print("❌ ERROR AL GENERAR LA PLANILLA PDF:")
        traceback.print_exc()
        print("="*40 + "\n")
        return jsonify({"message": f"Error interno: {str(err)}"}), 500
    finally:
        cursor.close()