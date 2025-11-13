from flask import Blueprint, jsonify, request, Response
from database.PeriodoInscripcion import PeriodoInscripcionRep
from database.PeriodoEscolar import PeriodoEscolarRep
from models.Usuario import Rol
from models.PeriodoInscripcion import PeriodoInscripcion
from models.PeriodoEscolar import PeriodoEscolar
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from datetime import datetime
from utils.handler import exception_handler
from database.Auditoria import Auditoria, AuditoriaRep

rep = PeriodoInscripcionRep()
escolar_rep = PeriodoEscolarRep()
logger = Logger()

reg_term_bp = Blueprint("registration_term", __name__)

@reg_term_bp.route("/registration/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not data or (not any(key in data for key in ("FechaInicio", "FechaFin"))):
            raise MissingEntityData("No se recibieron datos")
        if not "FechaInicio" in data or not "FechaFin" in data:
            raise MissingEntityData("Faltan datos para realizar la operación")
        elif not Validations.is_date(data["FechaInicio"]) or not Validations.is_date(data["FechaFin"]):
            raise ValidationError("Los formatos de las fechas son inválidos (YYYY-MM-DD)")
        
        registration_term = escolar_rep.get_latest()
        format = "%Y-%m-%d"
        date_dict = {
            "Inicio": datetime.strptime(data["FechaInicio"], format).date(),
            "Fin": datetime.strptime(data["FechaFin"], format).date(),
            "PeriodoEscolar": registration_term
        }
        reg = PeriodoInscripcion(date_dict)
        reg_id = rep.create(reg)

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": "Período de inscripción creado"
        }))

        return jsonify({"id": reg_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@reg_term_bp.route("/registration/get", methods=["GET"])
@reg_term_bp.route("/registration/get/<string:id>", methods=["GET"])
def get(id=None):
    try:
        if not id:
            entity = rep.get_latest()
        else:
            payload = Security.verify_token(request.headers)

            if not payload or payload["role"] != Rol.ADMIN.name:
                raise Unauthorized()
            elif not Validations.is_uuid(id):
                raise InvalidId(f"Invalid \"Inscripcion\" ID: {id}")
            entity = rep.get(id)
        return jsonify(entity.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@reg_term_bp.route("/registration/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        offset = request.args.get("offset")
        limit = request.args.get("limit")
        if offset != None:
            offset = int(offset)
        if limit != None:
            limit = int(limit)

        data = rep.list(offset, limit)

        if data == None or len(data) == 0:
            raise EntityNotFound("No hay inscripciones disponibles")
        
        return jsonify([d.to_dict() for d in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@reg_term_bp.route("/registration/update", methods=["PATCH"])
def update():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not data or not any(key in data for key in ("PeriodoInscripcionId", "FechaInicio", "FechaFin")):
            raise MissingEntityData("No se recibieron datos")
        elif not any(key in data for key in ("FechaInicio", "FechaFin")):
            raise MissingEntityData("Faltan datos para realizar la operación")
        elif "Inicio" in data and not Validations.is_date(data["FechaInicio"]):
            raise ValidationError("El formato de la fecha de inicio es inválido (YYYY-MM-DD)")
        elif "Fin" in data and not Validations.is_date(data["FechaFin"]):
            raise ValidationError("El formato de la fecha de fin es inválido (YYYY-MM-DD)")
        elif not Validations.is_uuid(data["PeriodoInscripcionId"]):
            raise InvalidId("El ID es inválido")
        
        format = "%Y-%m-%d"
        date_dict = {
            "id": data["PeriodoInscripcionId"],
        }
        if "FechaInicio" in data: date_dict["Inicio"] = datetime.strptime(data["FechaInicio"], format).date()
        if "FechaFin" in data: date_dict["Fin"] = datetime.strptime(data["FechaFin"], format).date()
        reg = PeriodoInscripcion(date_dict)
        affected = rep.update(reg)
        if not affected:
            raise EntityUpdateError("Ocurrio un error en la base de datos")
        
        AuditoriaRep().create(Auditoria({
            "Accion": "Acualización",
            "Descripcion": "Período de inscripción actualizado"
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@reg_term_bp.route("/registration/count", methods=["GET"])
def registrationCount():
    try:
        payload = Security.verify_token(request.headers);
    
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        return jsonify({"count": 0}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
