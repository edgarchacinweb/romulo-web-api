from flask import Blueprint, jsonify, request, Response
from database.Docente import DocenteRep
from models.Docente import Docente
from models.DatosPersona import DatosPersona
from models.Materia import Materia
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from models.Usuario import Usuario, Rol
from models.Auditoria import Auditoria
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from database.connection import Connection
from bcrypt import hashpw, gensalt
from os import getenv

rep = DocenteRep()
logger = Logger()
auditory = AuditoriaRep()

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/teacher/create", methods=["POST"])
def create_teacher():
    conn = Connection().get_connection()
    cursor = conn.cursor()

    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if "Nombre" not in data or not data["Nombre"]:
            raise MissingEntityData("El nombre del docente es requerido")
        elif not Validations.is_name(data["Nombre"]):
            raise ValidationError("El nombre del docente tiene un formato incorrecto")
        elif "Apellido" not in data or not data["Apellido"]:
            raise MissingEntityData("El apellido del docente es requerido")
        elif not Validations.is_lastname(data["Apellido"]):
            raise ValidationError("El apellido del docente tiene un formato incorrecto")
        elif "Sexo" not in data or not data["Sexo"]:
            raise MissingEntityData("El sexo del docente es requerido")
        elif not Validations.is_gender(data["Sexo"]):
            raise ValidationError("El sexo del docente tiene un formato incorrecto")
        elif "Cedula" not in data or not data["Cedula"]:
            raise MissingEntityData("La cédula del docente es requerida")
        elif not Validations.is_ci(data["Cedula"]):
            raise ValidationError("La cédula del docente tiene un formato incorrecto")
        elif "Telefono" not in data or not data["Telefono"]:
            raise MissingEntityData("El teléfono del docente es requerido")
        elif "Ocupacion" not in data or not data["Ocupacion"]:
            raise MissingEntityData("La ocupación del docente es requerida")
        elif "Direccion" not in data or not data["Direccion"]:
            raise MissingEntityData("La dirección del docente es requerida")
        elif not Validations.is_phone(data["Telefono"]):
            raise ValidationError("El teléfono del docente tiene un formato incorrecto")
        elif "Email" not in data or not data["Email"]:
            raise MissingEntityData("El email del docente es requerido")
        elif not Validations.is_email(data["Email"]):
            raise ValidationError("El email del docente tiene un formato incorrecto")
        elif "Horas" not in data or not data["Horas"]:
            raise MissingEntityData("Las horas del docente son requeridas")
        elif not Validations.is_teacher_hours(data["Horas"]):
            raise ValidationError("Las horas del docente tienen un formato incorrecto")
        elif "Materias" not in data or len(data["Materias"]) == 0:
            raise MissingEntityData("Las materias del docente son requeridas")
        else:
            for materia in data["Materias"]:
                if not Validations.is_uuid(materia):
                    raise ValidationError("El ID de la materia es inválido")

        # Creando registro de datos del docente
        cursor.execute(
            """
            INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Telefono", "Ocupacion", "Direccion")
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING "DatosPersonaId"
            """,
            (data["Nombre"], data["Apellido"], data["Sexo"], data["Cedula"], data["Telefono"], data["Ocupacion"], data["Direccion"])
        )

        id_datos_persona = cursor.fetchone()[0]
        
        if not id_datos_persona:
            raise EntityNotFound("Error al registrar los datos del docente")

        pwd = hashpw(f"V#{data['Cedula']}".encode("utf-8"), gensalt(rounds=int(getenv("pwd_rounds"))))

        # Creando registro de docente
        cursor.execute(
            """
            INSERT INTO "Docente" ("HorasAcademicas", "DatosPersonaId")
            VALUES (%s, %s) RETURNING "DocenteId"
            """,
            (data["Horas"], id_datos_persona)
        )

        id_docente = cursor.fetchone()[0]
        
        if not id_docente:
            raise EntityNotFound("Error al registrar el docente")

        # Vinculando materias al docente
        for materia in data["Materias"]:
            cursor.execute(
                """
                INSERT INTO "DocenteMateria" ("DocenteId", "MateriaId")
                VALUES (%s, %s)
                """,
                (id_docente, materia)
            )

        if not cursor.rowcount:
            raise EntityNotFound("Error al vincular las materias al docente")

        # Creando registro de usuario
        cursor.execute(
            """
            INSERT INTO "Usuario" ("Email", "Clave", "Rol", "DatosPersona")
            VALUES (%s, %s, %s, %s) RETURNING "UsuarioId"
            """,
            (data["Email"], pwd, Rol.TEACHER.value, id_datos_persona)
        )

        id_usuario = cursor.fetchone()[0]

        if not id_usuario:
            raise EntityNotFound("Error al registrar el usuario del docente")

        # Registrando auditoría
        cursor.execute(
            """
            INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion")
            VALUES (%s, %s, %s) RETURNING "AuditoriaId"
            """,
            (id_usuario, f"Docente {data['Nombre']} {data['Apellido']} registrado exitosamente", "Registro")
        )

        id_auditoria = cursor.fetchone()[0]

        if not id_auditoria:
            raise EntityNotFound("Error al registrar la auditoría")

        conn.commit()

        return Response(
            status=201
        )
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/get/<string:id>", methods=["GET"])
def get_teacher(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        teacher = rep.get(id)
        return jsonify(teacher.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@teacher_bp.route("/teacher/delete/<string:identity>", methods=["DELETE"])
def delete_teacher(identity: str):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_ci(identity):
            raise InvalidId(f"La cédula de identidad tiene un formato inválido")

        rep.delete(identity)

        auditory.create(Auditoria({
            "Accion": "Eliminación",
            "Descripcion": "Materia deshabilitada al docente"
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@teacher_bp.route("/teacher/update", methods=["PUT"])
def update_teacher():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not any(key in data for key in ("id", "UsuarioId", "MateriaId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_uuid(data["id"]):
            raise InvalidId("El ID del docente es inválido")
        elif not Validations.is_uuid(data["UsuarioId"]):
            raise InvalidId("El ID de usuario del docente es inválido")
        elif not Validations.is_uuid(data["MateriaId"]):
            raise InvalidId("El ID de la materia es inválido")

        docente = Docente(data)

        affected = rep.update(docente)

        if not affected:
            raise EntityUpdateError("Ocurrido un error al intentar actualizar el docente")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@teacher_bp.route("/teacher/filter", methods=["GET"])
def filter_teachers():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        offset = None
        limit = None

        if "from" in request.args:
            offset = request.args.get("from")
        if "limit" in request.args:
            limit = request.args.get("limit")

        filters = dict()

        if "Nombre" in request.args:
            filters["Nombre"] = request.args.get("Nombre")
            if not Validations.is_name(filters["Nombre"]):
                raise ValidationError("El nombre del docente tiene un formato incorrecto")
        if "Apellido" in request.args:
            filters["Apellido"] = request.args.get("Apellido")
            if not Validations.is_lastname(filters["Apellido"]):
                raise ValidationError("El apellido del docente tiene un formato incorrecto")
        if "Sexo" in request.args:
            filters["Sexo"] = request.args.get("Sexo")
        if "Cedula" in request.args:
            logger.debug(request.args)
            filters["Cedula"] = request.args.get("Cedula")
            if not Validations.is_ci(filters["Cedula"]):
                raise ValidationError("El número de Cédula del docente tiene un formato incorrecto")
        if "Telefono" in request.args:
            filters["Telefono"] = request.args.get("Telefono")
            if not Validations.is_phone(filters["Telefono"]):
                raise ValidationError("El número de teléfono del docente tiene un formato incorrecto")
        if "Materia" in request.args:
            filters["Materia"] = request.args.get("Materia")
            if not Validations.is_subject(filters["Materia"]):
                raise ValidationError("El nombre de la materia tiene un formato incorrecto")

        teachers = rep.list(limit, offset, filters)

        return jsonify({"total": len(teachers), "resultados":[t.to_dict() for t in teachers]}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@teacher_bp.route("/teacher/list", methods=["GET"])
def list_teachers():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        teachers = rep.get_all()

        return jsonify([t.to_dict() for t in teachers]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@teacher_bp.route("/teacher/subject", methods=["POST"])
def create_teacher_by_ci():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not any(key in data for key in ("Cedula", "Materia")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_ci(data["Cedula"]):
            raise ValidationError("El número de Cédula del docente tiene un formato incorrecto")
        elif not Validations.is_subject(data["Materia"]):
            raise InvalidId("El nombre de la materia tiene un formato inválido")

        id = rep.add_subject(data["Cedula"], data["Materia"])

        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@teacher_bp.route("/teacher/subject", methods=["DELETE"])
def remove_teacher_by_ci():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if any(key not in data for key in ("Cedula", "Materia")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_ci(data["Cedula"]):
            raise ValidationError("El número de Cédula del docente tiene un formato incorrecto")
        elif not Validations.is_subject(data["Materia"]):
            raise InvalidId("El nombre de la materia tiene un formato inválido")

        rep.remove_subject(data["Cedula"], data["Materia"])

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@teacher_bp.route("/teacher/count", methods=["GET"])
def count():
    try:
        count = rep.count()
        return jsonify({"count": count}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
