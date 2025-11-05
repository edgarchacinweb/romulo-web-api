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

rep = DocenteRep()
logger = Logger()
auditory = AuditoriaRep()

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/teacher/create", methods=["POST"])
def create_teacher():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != "ADMIN":
            raise Unauthorized()

        data = request.get_json()

        if not any(key in data for key in ("DatosPersonaId", "MateriaId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de usuario del docente es inválido")
        elif not Validations.is_uuid(data["MateriaId"]):
            raise InvalidId("El ID de la materia es inválido")

        docente = Docente({
            "DatosPersona": DatosPersona({"id": data["DatosPersonaId"]}),
            "Materia": Materia({"id": data["MateriaId"]})   
        })

        id = rep.create(docente)

        auditory.create(Auditoria({
            "Accion": "Registro",
            "Descripcion": "Materia vinculada a docente"
        }))

        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

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
