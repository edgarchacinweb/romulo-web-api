from flask import Blueprint, jsonify, request, Response, render_template
from werkzeug.utils import secure_filename
from database.connection import Connection
from database.Estudiante import EstudianteRep
from database.DatosPersona import DatosPersonaRep
from database.Usuario import Usuario, UsuarioRep
from database.Auditoria import Auditoria, AuditoriaRep
from database.Curso import CursoRep, Curso
from database.Clase import ClaseRep, Clase
from models.Estudiante import Estudiante
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.image import resize, get_format, convert_to_webp
from models.Usuario import Rol
from models.DatosPersona import DatosPersona
from models.Curso import Curso
from utils.handler import exception_handler
from datetime import datetime
from utils.config import app
from utils.helpers import number_to_letter
from utils.email import send_email
import os

rep = EstudianteRep()
logger = Logger()

student_bp = Blueprint("student", __name__)

@student_bp.route("/students/check_period", methods=["GET"])
def check_period():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        # Seleccionamos el PeriodoEscolarId asociado a la inscripción activa
        cursor.execute("""
            SELECT "PeriodoEscolarId" FROM "PeriodoInscripcion" 
            WHERE "Activo" = TRUE 
            AND CURRENT_DATE BETWEEN "Inicio" AND "Fin" 
            LIMIT 1;
        """)
        row = cursor.fetchone()
        
        if row:
            return jsonify({"open": True, "periodoEscolarId": row[0]}), 200
        return jsonify({"open": False, "message": "Proceso de inscripción cerrado"}), 404
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/create", methods=["POST"])
def create():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.PARENT.name]:
            raise Unauthorized()

        cursor.execute("""
            SELECT 1 FROM "PeriodoInscripcion" 
            WHERE "Activo" = TRUE AND CURRENT_DATE BETWEEN "Inicio" AND "Fin" LIMIT 1;
        """)
        if not cursor.fetchone():
            return jsonify({"message": "El proceso de inscripción se encuentra cerrado actualmente."}), 403

        data = request.form 
        files = request.files

        required_fields = ["Nombre", "Apellido", "Genero", "Cedula", "FechaNacimiento", 
                           "Parentesco", "Direccion", "IdRepresentante", "IdCurso"]
        
        for field in required_fields:
            if field not in data:
                raise MissingEntityData(f"Falta el campo requerido: {field}")

        cursor.execute(
            """INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Direccion") 
               VALUES (%s,%s,%s,%s,%s) RETURNING "DatosPersonaId";""",
            (data["Nombre"], data["Apellido"], data["Genero"], data["Cedula"], data["Direccion"])
        )
        datos_persona_id = cursor.fetchone()[0]

        cursor.execute(
            """INSERT INTO "Estudiante" ("FechaNacimiento", "Parentesco", "DatosPersonaId", "RepresentanteId") 
               VALUES (%s,%s,%s,%s) RETURNING "EstudianteId";""",
            (data["FechaNacimiento"], data["Parentesco"], datos_persona_id, data["IdRepresentante"])
        )
        estudiante_id = cursor.fetchone()[0]

        cursor.execute("""INSERT INTO "EstadoEstudiante" ("EstudianteId", "Estado") VALUES (%s, %s)""", (estudiante_id, 'revision'))
        cursor.execute("CALL registrar_curso_estudiante(%s, %s)", (estudiante_id, data["IdCurso"]))
        
        cursor.execute(
            """INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion") 
               VALUES ((SELECT "UsuarioId" FROM "Usuario" WHERE "DatosPersona" = %s), %s, %s)""",
            (data["IdRepresentante"], "Se registro un nuevo estudiante", "Registro")
        )

        foto = files["FotoCarnet"]
        if get_format(foto.filename) != "webp":
            foto = convert_to_webp(foto)
        
        full_path_carnet = os.path.join(app.config["UPLOAD_FOLDER"], f"carnet-{estudiante_id}.webp")
        resize(foto).save(full_path_carnet)
        
        if files.get("DocDni"):
            files.get("DocDni").save(os.path.join(app.config["UPLOAD_FOLDER"], f"dni-{estudiante_id}.pdf"))

        files["DocPartidaNacimiento"].save(os.path.join(app.config["UPLOAD_FOLDER"], f"partida-nacimiento-{estudiante_id}.pdf"))
        files["DocNotasCertificadas"].save(os.path.join(app.config["UPLOAD_FOLDER"], f"notas-certificadas-{estudiante_id}.pdf"))

        connection.commit()
        return jsonify({"message": "Estudiante registrado exitosamente"}), 201

    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in (Rol.ADMIN.name, Rol.PARENT.name): raise Unauthorized()
        
        cursor.execute("""
            SELECT dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", dp."Direccion",
                   e."FechaNacimiento", e."Parentesco", ce."CursoId"
            FROM "Estudiante" AS e
            INNER JOIN "DatosPersona" AS dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            LEFT JOIN "CursoEstudiante" AS ce ON e."EstudianteId" = ce."EstudianteId"
            WHERE e."EstudianteId" = %s
        """, (id,))
        
        row = cursor.fetchone()
        if not row: raise EntityNotFound("Estudiante no encontrado")

        return jsonify({
            "DatosPersona": {"Nombre": row[0], "Apellido": row[1], "Sexo": row[2], "Cedula": row[3], "Direccion": row[4]},
            "FechaNacimiento": str(row[5]),
            "Parentesco": row[6],
            "Curso": {"CursoId": row[7]}
        }), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/approve/<string:student_id>", methods=["PUT"])
def approve_student(student_id: str):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='inscrito' WHERE \"EstudianteId\"=%s;", (student_id,))
        cursor.execute("UPDATE \"Estudiante\" SET \"Activo\"=TRUE WHERE \"EstudianteId\"=%s;", (student_id,))
        connection.commit()
        return Response(status=204)
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/reject/<string:student_id>", methods=["PUT"])
def reject_student(student_id: str):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        data = request.get_json()
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='rechazado' WHERE \"EstudianteId\"=%s;", (student_id,))
        cursor.execute("UPDATE \"Estudiante\" SET \"Activo\"=FALSE WHERE \"EstudianteId\"=%s;", (student_id,))
        connection.commit()

        try:
            html = render_template("reject-email.html", motivo=data["Motivo"], descripcion=data["Descripcion"], date=datetime.now().strftime("%d/%m/%Y"))
            send_email(data["Email"], data["Motivo"], html, data["Descripcion"])
        except: pass
        return Response(status=204)
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/correct_application/<string:student_id>", methods=["PUT"])
def correct_application(student_id: str):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        data = request.form
        cursor.execute('SELECT "DatosPersonaId" FROM "Estudiante" WHERE "EstudianteId" = %s', (student_id,))
        dp_id = cursor.fetchone()[0]
        
        cursor.execute("""UPDATE "DatosPersona" SET "Nombre"=%s, "Apellido"=%s, "Sexo"=%s, "Cedula"=%s, "Direccion"=%s WHERE "DatosPersonaId"=%s;""",
            (data["Nombre"], data["Apellido"], data["Genero"], data["Cedula"], data["Direccion"], dp_id))
        
        cursor.execute("""UPDATE "Estudiante" SET "FechaNacimiento"=%s, "Parentesco"=%s, "Activo"=TRUE WHERE "EstudianteId"=%s;""",
                       (data["FechaNacimiento"], data["Parentesco"], student_id))

        cursor.execute("""UPDATE "EstadoEstudiante" SET "Estado"='revision' WHERE "EstudianteId"=%s;""", (student_id,))

        connection.commit()
        return jsonify({"message": "Solicitud corregida exitosamente."}), 200
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/change_status/<string:student_id>", methods=["PUT"])
def change_status(student_id: str):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        data = request.get_json()
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"=%s WHERE \"EstudianteId\"=%s;", (data.get("Estado"), student_id))
        connection.commit()
        return jsonify({"message": "Estado actualizado"}), 200
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

# --- CORRECCIÓN CLAVE: Usamos ce."PeriodoEscolarId" (tabla intermedia) ---
@student_bp.route("/students/by_parent/<string:parent_id>", methods=["GET"])
def get_all_by_parent(parent_id: str):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT ON (e."EstudianteId") 
                   ce."EstudianteId", e."FechaNacimiento", c."CursoId", c."Grado", ce."Seccion",
                   dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", ee."Estado", ce."PeriodoEscolarId"
            FROM "Estudiante" AS e 
            INNER JOIN "CursoEstudiante" AS ce ON ce."EstudianteId"=e."EstudianteId" 
            INNER JOIN "Curso" AS c ON c."CursoId"=ce."CursoId" 
            INNER JOIN "DatosPersona" AS dp ON e."DatosPersonaId"=dp."DatosPersonaId" 
            INNER JOIN "EstadoEstudiante" AS ee ON ee."EstudianteId"=e."EstudianteId" 
            WHERE e."RepresentanteId"=%s
            ORDER BY e."EstudianteId", c."Grado" DESC;""", (parent_id,))
            
        students = cursor.fetchall()
        
        return jsonify([{
            "EstudianteId": s[0], "FechaNacimiento": s[1],
            "Curso": {
                "CursoId": s[2], 
                "Grado": s[3], 
                "Seccion": number_to_letter(s[4]), 
                "PeriodoEscolarId": s[10] # Correctamente mapeado desde ce
            },
            "DatosPersona": {"Nombre": s[5], "Apellido": s[6], "Sexo": s[7], "Cedula": s[8]},
            "EstadoEstudiante": {"Estado": s[9]}
        } for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/filter", methods=["POST"])
def filter_students():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        data = request.get_json()
        query = """SELECT e."EstudianteId", ee."Estado", e."Activo", e."FechaNacimiento", e."Parentesco",
                          dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", dp."Direccion",
                          r."Nombre", r."Apellido", u."Email", c."Grado", ce."Seccion", u."UsuarioId"
                   FROM "EstadoEstudiante" AS ee
                   INNER JOIN "Estudiante" AS e ON e."EstudianteId"=ee."EstudianteId"
                   INNER JOIN "DatosPersona" AS dp ON dp."DatosPersonaId"=e."DatosPersonaId"
                   INNER JOIN "DatosPersona" AS r ON r."DatosPersonaId"=e."RepresentanteId"
                   INNER JOIN "CursoEstudiante" AS ce ON ce."EstudianteId"=e."EstudianteId"
                   INNER JOIN "Curso" AS c ON c."CursoId"=ce."CursoId"
                   INNER JOIN "Usuario" AS u ON u."DatosPersona"=r."DatosPersonaId" """
        conditions = []
        params = []
        if data.get("Estado"):
            conditions.append("ee.\"Estado\" = %s")
            params.append(data["Estado"])
        if conditions: query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY ee.\"FechaCreacion\" DESC;"
        cursor.execute(query, params)
        students = cursor.fetchall()
        return jsonify([{
            "EstudianteId": s[0], "Estado": s[1], "Activo": s[2], "FechaNacimiento": str(s[3]),
            "DatosPersona": {"Nombre": s[5], "Apellido": s[6], "Sexo": s[7], "Cedula": s[8], "Direccion": s[9]},
            "Representante": {"Nombre": s[10], "Apellido": s[11], "Email": s[12], "UsuarioId": s[15]},
            "Curso": {"Grado": s[13], "Seccion": s[14]}
        } for s in students]), 200
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/reinscribe", methods=["POST"])
def reinscribe_student():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload: raise Unauthorized()

        # Validación con SELECT 1 (Segura)
        cursor.execute("""
            SELECT 1 FROM "PeriodoInscripcion" 
            WHERE "Activo" = TRUE AND CURRENT_DATE BETWEEN "Inicio" AND "Fin" LIMIT 1;
        """)
        if not cursor.fetchone():
            return jsonify({"message": "Proceso de reinscripción cerrado."}), 403

        data = request.get_json()
        student_id = data.get("EstudianteId")
        new_curso_id = data.get("NuevoCursoId")

        if not student_id or not new_curso_id:
            raise MissingEntityData("Faltan datos para procesar la reinscripción")

        cursor.execute("""
            UPDATE "EstadoEstudiante" SET "Estado" = 'revision' 
            WHERE "EstudianteId" = %s;
        """, (student_id,))

        cursor.execute("CALL registrar_curso_estudiante(%s, %s)", (student_id, new_curso_id))

        cursor.execute(
            """INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion") 
               VALUES (%s, %s, %s)""",
            (payload["id"], "Se proceso una reinscripción automática", "Actualización")
        )

        connection.commit()
        return jsonify({"message": "Reinscripción procesada exitosamente. Su solicitud está en revisión."}), 200
    except Exception as err:
        connection.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()