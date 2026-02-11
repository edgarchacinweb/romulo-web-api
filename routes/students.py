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

@student_bp.route("/students/create", methods=["POST"])
def create():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    
    # Inicializamos las rutas de archivos a None para evitar errores en el 'except'
    # si la ejecución falla antes de definirlos.
    full_path_carnet = None
    full_path_dni = None
    full_path_partida = None
    full_path_notas = None

    try:
        # 1. Autenticación
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.PARENT.name]:
            raise Unauthorized()

        # 2. Extracción de Datos (CORRECCIÓN A: Usar request.form para multipart)
        # request.form se comporta como un diccionario para los campos de texto
        data = request.form 
        files = request.files

        # 3. Validaciones (Simplificadas para legibilidad)
        required_fields = ["Nombre", "Apellido", "Genero", "Cedula", "FechaNacimiento", 
                           "Parentesco", "Direccion", "IdRepresentante", "IdCurso"]
        
        allowed_parentesco = ['Madre', 'Padre', 'Abuelo/a', 'Tío/a', 'Hermano/a', 'Padrastro', 'Madrastra', 'Tutor Legal', 'Otro']

        for field in required_fields:
            if field not in data:
                raise MissingEntityData(f"Falta el campo requerido: {field}")

        if data["Parentesco"] not in allowed_parentesco:
            raise ValidationError(f"\"{data['Parentesco']}\" no es un parentesco válido")

        # Validar estudiante duplicado
        cursor.execute(
            """SELECT e."EstudianteId" FROM "Estudiante" AS e
                INNER JOIN "DatosPersona" AS dp ON e."DatosPersonaId"=dp."DatosPersonaId"
                WHERE dp."Nombre"=%s AND dp."Apellido"=%s AND dp."Sexo"=%s AND e."RepresentanteId"=%s AND e."FechaNacimiento"=%s AND e."Parentesco"=%s;""",
            (data["Nombre"], data["Apellido"], data["Genero"], data["IdRepresentante"], data["FechaNacimiento"], data["Parentesco"])
        )
        row = cursor.fetchone()
        if row:
            raise ValidationError("El estudiante ya existe")

        # Validación de existencia de archivos
        required_files = ["FotoCarnet", "DocPartidaNacimiento", "DocNotasCertificadas"]
        for file_key in required_files:
            if file_key not in files:
                raise MissingEntityData(f"Falta el archivo: {file_key}")

        # 4. Inserciones en Base de Datos (SIN COMMIT AÚN)
        # Mantenemos la transacción abierta para obtener los IDs
        
        cursor.execute(
            """INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Direccion") 
               VALUES (%s,%s,%s,%s,%s) RETURNING "DatosPersonaId";""",
            (data["Nombre"], data["Apellido"], data["Genero"], data["Cedula"], data["Direccion"])
        )
        row = cursor.fetchone()
        if not row: raise EntityExceptions.EntityNotFound("Error al crear DatosPersona")
        datos_persona_id = row[0]

        cursor.execute(
            """INSERT INTO "Estudiante" ("FechaNacimiento", "Parentesco", "DatosPersonaId", "RepresentanteId") 
               VALUES (%s,%s,%s,%s) RETURNING "EstudianteId";""",
            (data["FechaNacimiento"], data["Parentesco"], datos_persona_id, data["IdRepresentante"])
        )
        row = cursor.fetchone()
        if not row: raise EntityExceptions.EntityNotFound("Error al crear Estudiante")
        estudiante_id = row[0]

        cursor.execute(
            """INSERT INTO "EstadoEstudiante" ("EstudianteId", "Estado") 
               VALUES (%s, %s) RETURNING "EstadoEstudianteId";""",
            (estudiante_id, 'revision')
        )

        cursor.execute(
            "CALL registrar_curso_estudiante(%s, %s)",
            (estudiante_id, data["IdCurso"])
        )
        
        # Auditoría (Simplificada)
        cursor.execute(
            """INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion") 
               VALUES ((SELECT "UsuarioId" FROM "Usuario" WHERE "DatosPersona" = %s), %s, %s)""",
            (data["IdRepresentante"], "Se registro un nuevo estudiante", "Registro")
        )

        # 5. Procesamiento de Archivos (CORRECCIÓN B: Antes del Commit)
        # Usamos el estudiante_id que obtuvimos de la transacción abierta
        
        # --- FOTO CARNET ---
        foto = files["FotoCarnet"]
        # Asumo que tus funciones auxiliares (get_format, convert_to_webp) existen y funcionan
        if get_format(foto.filename) not in ["png", "jpg", "jpeg", "webp"]:
            raise ValidationError("Formato de foto inválido")
        elif get_format(foto.filename) != "webp":
            foto = convert_to_webp(foto)
        
        nombre_carnet = f"carnet-{estudiante_id}.webp"
        full_path_carnet = os.path.join(app.config["UPLOAD_FOLDER"], nombre_carnet)
        resized_foto = resize(foto)
        resized_foto.save(full_path_carnet)
        
        # --- DOCUMENTOS PDF ---
        # Definimos los nombres y rutas
        docDni = files.get("DocDni")
        if docDni:
            nombre_dni = f"dni-{estudiante_id}.pdf"
            full_path_dni = os.path.join(app.config["UPLOAD_FOLDER"], nombre_dni)
            docDni.save(full_path_dni)

        nombre_partida = f"partida-nacimiento-{estudiante_id}.pdf"
        full_path_partida = os.path.join(app.config["UPLOAD_FOLDER"], nombre_partida)
        files["DocPartidaNacimiento"].save(full_path_partida)

        nombre_notas = f"notas-certificadas-{estudiante_id}.pdf"
        full_path_notas = os.path.join(app.config["UPLOAD_FOLDER"], nombre_notas)
        files["DocNotasCertificadas"].save(full_path_notas)

        # 6. COMMIT FINAL
        # Solo llegamos aquí si la DB insertó Y los archivos se guardaron en disco.
        connection.commit()

        return jsonify({"message": "Estudiante registrado exitosamente"}), 201

    except Exception as err:
        # 7. Manejo de Errores y Limpieza (Rollback + Borrado físico)
        connection.rollback()
        
        # Borrar archivos si se llegaron a crear (CORRECCIÓN C: Variables seguras)
        files_to_delete = [full_path_carnet, full_path_dni, full_path_partida, full_path_notas]
        for path in files_to_delete:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass # Loggear esto en producción

        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
        
    finally:
        cursor.close()


@student_bp.route("/students/update", methods=["PUT"])
def update():
    conn = Connection().get_connection();
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        data = request.get_json()
        
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/count/by_parent", methods=["GET"])
def get_by_parent():
    conn = Connection().get_connection()
    cursor = conn.cursor()

    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.PARENT.name:
            raise Unauthorized()

        parent_id = payload["id"]

        if not Validations.is_uuid(parent_id):
            raise InvalidId(f"ID inválido: {parent_id}")
        
        cursor.execute("SELECT COUNT(\"EstudianteId\") FROM \"Estudiante\" WHERE \"RepresentanteId\"=%s;", (parent_id,))
        count = cursor.fetchone()[0]

        if not count:
            count = 0
        
        return jsonify({"count": count}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/by_parent/<string:parent_id>", methods=["GET"])
def get_all_by_parent(parent_id: str):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.PARENT.name:
            raise Unauthorized()

        if not Validations.is_uuid(parent_id):
            raise InvalidId(f"ID inválido: {parent_id}")
        
        cursor.execute("SELECT * FROM \"CursoEstudiante\" AS ce INNER JOIN \"Curso\" AS c ON c.\"CursoId\"=ce.\"CursoId\" INNER JOIN \"Estudiante\" AS e ON ce.\"EstudianteId\"=e.\"EstudianteId\" INNER JOIN \"DatosPersona\" AS dp ON e.\"DatosPersonaId\"=dp.\"DatosPersonaId\" INNER JOIN \"EstadoEstudiante\" AS ee ON ee.\"EstudianteId\"=e.\"EstudianteId\" WHERE e.\"RepresentanteId\"=%s;", (parent_id,))
        students = cursor.fetchall()
        logger.debug(students, "students")

        return jsonify([{
            "EstudianteId": s[0],
            "FechaNacimiento": s[8],
            "Curso": {
                "CursoId": s[1],
                "Grado": s[6],
                "Seccion": number_to_letter(s[2])
            },
            "DatosPersona": {
                "Nombre": s[15],
                "Apellido": s[16],
                "Sexo": s[17],
                "Cedula": s[18]
            },
            "EstadoEstudiante": {
                "EstadoEstudianteId": s[24],
                "Estado": s[26]
            }
        } for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/filter", methods=["POST"])
def filter_students():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()
        
        if "CursoId" in data and data["CursoId"] and not Validations.is_uuid(data["CursoId"]):
            raise ValidationError("El ID del curso es inválido.")
        elif "Estado" in data and not data["Estado"] in ("revision", "inscrito", "retirado", "graduado"):
            raise ValidationError("El estado del estudiante es inválido.")
        elif "Busqueda" in data and data["Busqueda"] and not Validations.is_name(data["Busqueda"]) and not Validations.is_ci(data["Busqueda"]):
            raise ValidationError("La busqueda ingresada no es un nombre ni una cédula.")
        elif "Seccion" in data and data["Seccion"] and not Validations.is_section(data["Seccion"]):
            raise ValidationError("La sección es inválida.")
        
        query = """SELECT * FROM "EstadoEstudiante" AS ee
                    INNER JOIN "Estudiante" AS E ON e."EstudianteId"=ee."EstudianteId"
                    INNER JOIN "DatosPersona" AS dp ON dp."DatosPersonaId"=e."DatosPersonaId"
                    INNER JOIN "DatosPersona" AS r ON r."DatosPersonaId"=e."RepresentanteId"
                    INNER JOIN "CursoEstudiante" AS ce ON ce."EstudianteId"=e."EstudianteId"
                    INNER JOIN "Curso" AS c ON c."CursoId"=ce."CursoId"
                    INNER JOIN "Usuario" AS u ON u."DatosPersona"=r."DatosPersonaId" """
        
        if "CursoId" in data or "Estado" in data or "Busqueda" in data:
            query += "WHERE "

        if "CursoId" in data and data["CursoId"]:
            query += f"ce.\"CursoId\" = '{data['CursoId']}' AND "
        if "Estado" in data and data["Estado"]:
            query += f"ee.\"Estado\" = '{data['Estado']}' AND "
        if "Seccion" in data and data["Seccion"]:
            query += f"ce.\"Seccion\" = '{data['Seccion']}' AND "
        if "Busqueda" in data and data["Busqueda"] and Validations.is_ci(data["Busqueda"]):
            query += f"dp.\"Cedula\" = '{data['Busqueda']}' AND "
        elif "Busqueda" in data and data["Busqueda"]:
            splited_name = data["Busqueda"].split()
            name = splited_name[0]
            last_name = splited_name[-1]
            query += f"(dp.\"Nombre\" LIKE '%{name}%'"
            if len(splited_name) > 1:
                query += f" AND dp.\"Apellido\" LIKE '%{last_name}%'"
            query += ") AND "
        
        query = query.rsplit(" AND ", 1)[0] + "ORDER BY ee.\"Activo\" DESC, ee.\"FechaCreacion\" DESC;"
        logger.debug(query, "query")
        cursor.execute(query)
        students = cursor.fetchall()
        logger.debug(query, "students")

        return jsonify([{
            "EstudianteId": s[1],
            "Estado": s[2],
            "Activo": s[4],
            "FechaNacimiento": s[6],
            "Parentesco": s[7],
            "DatosPersona": {
                "DatosPersonaId": s[8],
                "Nombre": s[13],
                "Apellido": s[14],
                "Sexo": s[15],
                "Cedula": s[16],
                "Direccion": s[18]
            },
            "Representante": {
                "DatosPersonaId": s[22],
                "Nombre": s[23],
                "Apellido": s[24],
                "Sexo": s[25],
                "Cedula": s[26],
                "Telefono": s[27],
                "Direccion": s[28],
                "Ocupacion": s[29],
                "UsuarioId": s[39],
                "Email": s[40],
            },
            "Curso": {
                "CursoId": s[37],
                "Grado": s[38],
                "Seccion": s[34]
            }
        } for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/approve/<string:student_id>", methods=["PUT"])
def approve_student(student_id: str):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(student_id):
            raise InvalidId(f"ID inválido: {student_id}")
        
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='inscrito', \"Activo\"=TRUE WHERE \"EstudianteId\"=%s;", (student_id,))
        conn.commit()

        return Response(status=204)
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()


@student_bp.route("/students/reject/<string:student_id>", methods=["PUT"])
def reject_student(student_id: str):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(student_id):
            raise InvalidId(f"ID inválido: {student_id}")

        data = request.get_json()

        if "Email" not in data or not data["Email"]:
            raise ValidationError("Debes enviar un email para rechazar al estudiante.")
        elif "Email" in data and not Validations.is_email(data["Email"]):
            raise ValidationError("El email es inválido.")
        elif "Motivo" not in data or not data["Motivo"]:
            raise ValidationError("Debes enviar un motivo para rechazar al estudiante.")
        elif "Descripcion" not in data or not data["Descripcion"]:
            raise ValidationError("Debes enviar una descripción para rechazar al estudiante.")
        elif "Descripcion" in data and len(data["Descripcion"]) > 200:
            raise ValidationError("La descripción es muy larga.")
        elif "Descripcion" in data and len(data["Descripcion"]) < 10:
            raise ValidationError("La descripción es muy corta.")
        
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='revision', \"Activo\"=FALSE WHERE \"EstudianteId\"=%s;", (student_id,))
        conn.commit()

        html = render_template("reject-email.html", motivo=data["Motivo"], descripcion=data["Descripcion"], date=datetime.now().strftime("%A %d/%m/%Y"))

        send_email(data["Email"], data["Motivo"], html, data["Descripcion"])

        return Response(status=204)
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/count", methods=["GET"])
def count():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(\"EstudianteId\") FROM \"EstadoEstudiante\" WHERE \"Estado\"='inscrito'")
        count = cursor.fetchone()[0]

        if not count:
            count = 0
        
        return jsonify({"count": count}), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
