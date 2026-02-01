from flask import Blueprint, jsonify, request, Response
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
        if files["DocDni"]:
            nombre_dni = f"dni-{estudiante_id}.pdf"
            full_path_dni = os.path.join(app.config["UPLOAD_FOLDER"], nombre_dni)
            files["DocDni"].save(full_path_dni)

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


@student_bp.route("/students/create/parent_ci", methods=["POST"])
def create_parent_by_ci():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "CedulaRepresentante", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_ci(data["CedulaRepresentante"]):
            raise InvalidId("El ID del representante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        data["Activo"] = True
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

        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        estudiante = rep.get(id)

        if estudiante == None:
            raise EntityNotFound(f"No se encontró ningún estudiante con ese identificador")

        return jsonify(estudiante.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        offset = None
        limit = None

        if request.args.get("offset") != None:
            offset = int(request.args.get("offset"))
        if request.args.get("limit") != None:
            limit = int(request.args.get("limit"))

        students = rep.list(offset, limit)

        if not students:
            raise EntityNotFound("No se encontraron estudiantes registrados")

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        affected = rep.delete(id)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/update/<string:id>", methods=["PUT"])
def update(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        data = request.get_json()

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "RepresentanteId", "CursoId", "Activo")):
            raise MissingEntityData("No se recibieron datos suficientes")

        if not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_uuid(data["RepresentanteId"]):
            raise InvalidId("El ID del representante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")
        
        student = Estudiante(data)
        affected = rep.update(student)

        if not affected:
            raise EntityUpdateError("No se pudo actualizar los datos del estudiante")
        
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get_all", methods=["GET"])
def get_all():
    try:
        students = rep.get_all()
        logger.debug(students)
        return jsonify(students), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/create/parent", methods=["POST"])
def create_parent():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()
        
        if not Validations.is_ci(f"{data['CedulaRepresentante']}"):
            raise ValidationError(f"Cédula de identidad del representante inválida")
        
        parent_id = DatosPersonaRep().get_by_ci(data["CedulaRepresentante"])

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        student = Estudiante({
            "FechaNacimiento": data["FechaNacimiento"],
            "DatosPersonaId": data["DatosPersonaId"],
            "RepresentanteId": parent_id,
            "CursoId": data["CursoId"],
            "Activo": True
        })


        student_id = rep.create(student)

        if not student_id:
            raise InsertEntityError("Ocurrido un error al intentar registrar al estudiante")

        return jsonify({"id": student_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list/parent/<string:parent_id>", methods=["GET"])
def list_by_parent(parent_id: str = ""):
    try:
        if not Validations.is_uuid(parent_id):
            raise InvalidId(f"ID inválido: {parent_id}")

        students = rep.list_by_parent(parent_id)

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list_by_class/<string:classroom_id>", methods=["GET"])
def list_by_class(classroom_id: str):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        if not Validations.is_uuid(classroom_id):
            raise InvalidId(f"El identificador de la clase es inválido")
        
        students = rep.list_by_class(Clase({"id": classroom_id}))

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get/by_people/<string:id>", methods=["GET"])
def get_by_ci(id: str):
    try:
        data = rep.get_by_people(id);
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
