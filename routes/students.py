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
    
    # Inicializamos rutas
    full_path_carnet = None
    full_path_dni = None
    full_path_partida = None
    full_path_notas = None

    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.PARENT.name]:
            raise Unauthorized()

        data = request.form 
        files = request.files

        required_fields = ["Nombre", "Apellido", "Genero", "Cedula", "FechaNacimiento", 
                           "Parentesco", "Direccion", "IdRepresentante", "IdCurso"]
        allowed_parentesco = ['Madre', 'Padre', 'Abuelo/a', 'Tío/a', 'Hermano/a', 'Padrastro', 'Madrastra', 'Tutor Legal', 'Otro']

        for field in required_fields:
            if field not in data:
                raise MissingEntityData(f"Falta el campo requerido: {field}")

        if data["Parentesco"] not in allowed_parentesco:
            raise ValidationError(f"\"{data['Parentesco']}\" no es un parentesco válido")

        cursor.execute(
            """SELECT e."EstudianteId" FROM "Estudiante" AS e
                INNER JOIN "DatosPersona" AS dp ON e."DatosPersonaId"=dp."DatosPersonaId"
                WHERE dp."Nombre"=%s AND dp."Apellido"=%s AND dp."Sexo"=%s AND e."RepresentanteId"=%s AND e."FechaNacimiento"=%s AND e."Parentesco"=%s;""",
            (data["Nombre"], data["Apellido"], data["Genero"], data["IdRepresentante"], data["FechaNacimiento"], data["Parentesco"])
        )
        if cursor.fetchone():
            raise ValidationError("El estudiante ya existe")

        required_files = ["FotoCarnet", "DocPartidaNacimiento", "DocNotasCertificadas"]
        for file_key in required_files:
            if file_key not in files:
                raise MissingEntityData(f"Falta el archivo: {file_key}")

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

        cursor.execute("CALL registrar_curso_estudiante(%s, %s)", (estudiante_id, data["IdCurso"]))
        
        cursor.execute(
            """INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion") 
               VALUES ((SELECT "UsuarioId" FROM "Usuario" WHERE "DatosPersona" = %s), %s, %s)""",
            (data["IdRepresentante"], "Se registro un nuevo estudiante", "Registro")
        )

        # Archivos
        foto = files["FotoCarnet"]
        if get_format(foto.filename) not in ["png", "jpg", "jpeg", "webp"]:
            raise ValidationError("Formato de foto inválido")
        elif get_format(foto.filename) != "webp":
            foto = convert_to_webp(foto)
        
        nombre_carnet = f"carnet-{estudiante_id}.webp"
        full_path_carnet = os.path.join(app.config["UPLOAD_FOLDER"], nombre_carnet)
        resize(foto).save(full_path_carnet)
        
        if files.get("DocDni"):
            nombre_dni = f"dni-{estudiante_id}.pdf"
            full_path_dni = os.path.join(app.config["UPLOAD_FOLDER"], nombre_dni)
            files.get("DocDni").save(full_path_dni)

        nombre_partida = f"partida-nacimiento-{estudiante_id}.pdf"
        full_path_partida = os.path.join(app.config["UPLOAD_FOLDER"], nombre_partida)
        files["DocPartidaNacimiento"].save(full_path_partida)

        nombre_notas = f"notas-certificadas-{estudiante_id}.pdf"
        full_path_notas = os.path.join(app.config["UPLOAD_FOLDER"], nombre_notas)
        files["DocNotasCertificadas"].save(full_path_notas)

        connection.commit()
        return jsonify({"message": "Estudiante registrado exitosamente"}), 201

    except Exception as err:
        connection.rollback()
        for path in [full_path_carnet, full_path_dni, full_path_partida, full_path_notas]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except OSError: pass 
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@student_bp.route("/students/create/parent_ci", methods=["POST"])
def create_parent_by_ci():
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        
        data = request.get_json()
        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "CedulaRepresentante", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        
        estudiante = Estudiante({
            "FechaNacimiento": datetime.strptime(data["FechaNacimiento"], "%Y-%m-%d").date(),
            "DatosPersona": DatosPersona({"id": data["DatosPersonaId"]}),
            "Representante": DatosPersona({"Cedula": data["CedulaRepresentante"]}),
            "Curso": Curso({"id": data["CursoId"]})
        })
        rep.create_by_ci(estudiante)
        return Response(status=201)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)
        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name): raise Unauthorized()
        if not Validations.is_uuid(id): raise InvalidId(f"ID inválido: {id}")

        estudiante = rep.get(id)
        if estudiante == None: raise EntityNotFound(f"No se encontró ningún estudiante con ese identificador")

        return jsonify(estudiante.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        
        offset = int(request.args.get("offset")) if request.args.get("offset") else None
        limit = int(request.args.get("limit")) if request.args.get("limit") else None

        students = rep.list(offset, limit)
        if not students: raise EntityNotFound("No se encontraron estudiantes registrados")

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        if not Validations.is_uuid(id): raise InvalidId(f"ID inválido: {id}")

        if not rep.delete(id): return Response(status=404)
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/update/<string:id>", methods=["PUT"])
def update(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        if not Validations.is_uuid(id): raise InvalidId(f"ID inválido: {id}")

        data = request.get_json()
        if not data: raise MissingEntityData("No se recibieron datos")
        
        student = Estudiante(data)
        if not rep.update(student): raise EntityUpdateError("No se pudo actualizar")
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get_all", methods=["GET"])
def get_all():
    try:
        return jsonify(rep.get_all()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/create/parent", methods=["POST"])
def create_parent():
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        
        data = request.get_json()
        if not Validations.is_ci(f"{data['CedulaRepresentante']}"): raise ValidationError("Cédula inválida")
        
        parent_id = DatosPersonaRep().get_by_ci(data["CedulaRepresentante"])
        
        student = Estudiante({
            "FechaNacimiento": data["FechaNacimiento"],
            "DatosPersonaId": data["DatosPersonaId"],
            "RepresentanteId": parent_id,
            "CursoId": data["CursoId"],
            "Activo": True
        })

        student_id = rep.create(student)
        if not student_id: raise InsertEntityError("Error al registrar estudiante")

        return jsonify({"id": student_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list/parent/<string:parent_id>", methods=["GET"])
def list_by_parent(parent_id: str = ""):
    try:
        if not Validations.is_uuid(parent_id): raise InvalidId(f"ID inválido: {parent_id}")
        students = rep.list_by_parent(parent_id)
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list_by_class/<string:classroom_id>", methods=["GET"])
def list_by_class(classroom_id: str):
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]: raise Unauthorized()
        if not Validations.is_uuid(classroom_id): raise InvalidId(f"ID inválido")
        
        students = rep.list_by_class(Clase({"id": classroom_id}))
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get/by_people/<string:id>", methods=["GET"])
def get_by_ci(id: str):
    try:
        data = rep.get_by_people(id)
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/count", methods=["GET"])
def count():
    try:
        return jsonify({"count": rep.count()}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/count/by_parent", methods=["GET"])
def get_by_parent():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.PARENT.name: raise Unauthorized()
        
        cursor.execute("SELECT COUNT(\"EstudianteId\") FROM \"Estudiante\" WHERE \"RepresentanteId\"=%s;", (payload["id"],))
        row = cursor.fetchone()
        count = row[0] if row else 0
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
        if not payload or payload["role"] != Rol.PARENT.name: raise Unauthorized()
        if not Validations.is_uuid(parent_id): raise InvalidId(f"ID inválido")
        
        cursor.execute("SELECT * FROM \"CursoEstudiante\" AS ce INNER JOIN \"Curso\" AS c ON c.\"CursoId\"=ce.\"CursoId\" INNER JOIN \"Estudiante\" AS e ON ce.\"EstudianteId\"=e.\"EstudianteId\" INNER JOIN \"DatosPersona\" AS dp ON e.\"DatosPersonaId\"=dp.\"DatosPersonaId\" INNER JOIN \"EstadoEstudiante\" AS ee ON ee.\"EstudianteId\"=e.\"EstudianteId\" WHERE e.\"RepresentanteId\"=%s;", (parent_id,))
        students = cursor.fetchall()

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
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        
        data = request.get_json()
        
        # --- SOLUCIÓN: SELECT EXPLÍCITO (COLUMNA POR COLUMNA) ---
        query = """SELECT 
                    e."EstudianteId",       -- 0
                    ee."Estado",            -- 1
                    e."Activo",             -- 2
                    e."FechaNacimiento",    -- 3
                    e."Parentesco",         -- 4
                    dp."DatosPersonaId",    -- 5 (Estudiante)
                    dp."Nombre",            -- 6
                    dp."Apellido",          -- 7
                    dp."Sexo",              -- 8
                    dp."Cedula",            -- 9
                    dp."Direccion",         -- 10
                    r."DatosPersonaId",     -- 11 (Representante)
                    r."Nombre",             -- 12
                    r."Apellido",           -- 13
                    r."Sexo",               -- 14
                    r."Cedula",             -- 15
                    r."Telefono",           -- 16
                    r."Direccion",          -- 17
                    r."Ocupacion",          -- 18
                    u."UsuarioId",          -- 19
                    u."Email",              -- 20
                    c."CursoId",            -- 21
                    c."Grado",              -- 22
                    ce."Seccion"            -- 23
                   FROM "EstadoEstudiante" AS ee
                   INNER JOIN "Estudiante" AS e ON e."EstudianteId"=ee."EstudianteId"
                   INNER JOIN "DatosPersona" AS dp ON dp."DatosPersonaId"=e."DatosPersonaId"
                   INNER JOIN "DatosPersona" AS r ON r."DatosPersonaId"=e."RepresentanteId"
                   INNER JOIN "CursoEstudiante" AS ce ON ce."EstudianteId"=e."EstudianteId"
                   INNER JOIN "Curso" AS c ON c."CursoId"=ce."CursoId"
                   INNER JOIN "Usuario" AS u ON u."DatosPersona"=r."DatosPersonaId" """
        
        conditions = []

        if "CursoId" in data and data["CursoId"]:
            if not Validations.is_uuid(data["CursoId"]): raise ValidationError("ID Curso inválido")
            conditions.append(f"ce.\"CursoId\" = '{data['CursoId']}'")

        if "Estado" in data and data["Estado"]:
            conditions.append(f"ee.\"Estado\" = '{data['Estado']}'")

        if "Seccion" in data and data["Seccion"]:
            conditions.append(f"ce.\"Seccion\" = '{data['Seccion']}'")

        if "Busqueda" in data and data["Busqueda"]:
            if Validations.is_ci(data["Busqueda"]):
                conditions.append(f"dp.\"Cedula\" = '{data['Busqueda']}'")
            else:
                splited_name = data["Busqueda"].split()
                name_query = f"(dp.\"Nombre\" LIKE '%{splited_name[0]}%'"
                if len(splited_name) > 1:
                    name_query += f" AND dp.\"Apellido\" LIKE '%{splited_name[-1]}%'"
                name_query += ")"
                conditions.append(name_query)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY e.\"Activo\" DESC, ee.\"FechaCreacion\" DESC;"
        
        cursor.execute(query)
        students = cursor.fetchall()

        return jsonify([{
            "EstudianteId": s[0],
            "Estado": s[1],
            "Activo": s[2],
            "FechaNacimiento": str(s[3]), # Convertimos a string por seguridad
            "Parentesco": s[4],
            "DatosPersona": {
                "DatosPersonaId": s[5],
                "Nombre": s[6],
                "Apellido": s[7],
                "Sexo": s[8],
                "Cedula": s[9],
                "Direccion": s[10]
            },
            "Representante": {
                "DatosPersonaId": s[11],
                "Nombre": s[12],
                "Apellido": s[13],
                "Sexo": s[14],
                "Cedula": s[15],
                "Telefono": s[16],
                "Direccion": s[17],
                "Ocupacion": s[18],
                "UsuarioId": s[19],
                "Email": s[20],
            },
            "Curso": {
                "CursoId": s[21],
                "Grado": s[22],
                "Seccion": number_to_letter(s[23]) if isinstance(s[23], int) else s[23]
            }
        } for s in students]), 200
    except Exception as err:
        conn.rollback()
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
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        if not Validations.is_uuid(student_id): raise InvalidId(f"ID inválido")
        
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='inscrito' WHERE \"EstudianteId\"=%s;", (student_id,))
        cursor.execute("UPDATE \"Estudiante\" SET \"Activo\"=TRUE WHERE \"EstudianteId\"=%s;", (student_id,))
        
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
        if not payload or payload["role"] != Rol.ADMIN.name: raise Unauthorized()
        if not Validations.is_uuid(student_id): raise InvalidId(f"ID inválido")

        data = request.get_json()
        if "Email" not in data: raise ValidationError("Falta Email")
        
        cursor.execute("UPDATE \"EstadoEstudiante\" SET \"Estado\"='revision' WHERE \"EstudianteId\"=%s;", (student_id,))
        cursor.execute("UPDATE \"Estudiante\" SET \"Activo\"=FALSE WHERE \"EstudianteId\"=%s;", (student_id,))
        
        conn.commit()

        try:
            html = render_template("reject-email.html", motivo=data["Motivo"], descripcion=data["Descripcion"], date=datetime.now().strftime("%d/%m/%Y"))
            send_email(data["Email"], data["Motivo"], html, data["Descripcion"])
        except: pass

        return Response(status=204)
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()