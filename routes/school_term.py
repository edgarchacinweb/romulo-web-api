from flask import Blueprint, request, jsonify, Response
from models.PeriodoEscolar import PeriodoEscolar
from database.PeriodoEscolar import PeriodoEscolarRep
from models.Usuario import Usuario, Rol
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.exceptions import *
from utils.Security import Security
from utils.handler import exception_handler
from database.Auditoria import Auditoria, AuditoriaRep

school_term_bp = Blueprint("periodo_escolar", __name__)
logger = Logger()
rep = PeriodoEscolarRep()


@school_term_bp.route("/school_term/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data:
            raise MissingEntityData("No se recibieron datos")
        if not any(key in data for key in ("FechaInicio", "FechaFin", "Capacidad")):
            raise MissingEntityData("Faltan datos para realizar la operación")
        elif not Validations.is_date(data["FechaInicio"]):
            raise ValidationError("El formato de la fecha de inicio del período escolar es inválido")
        elif not Validations.is_date(data["FechaFin"]):
            raise ValidationError("El formato de la fecha de fin del período escolar es inválido")
        elif not Validations.is_capacity(data["Capacidad"]):
            raise ValidationError("La capacidad máxima de las secciones debe ser un número entero en el rango de 15 y 40")
        
        date_from = data["FechaInicio"]
        date_to = data["FechaFin"]

        term = PeriodoEscolar({
            "FechaInicio": date_from,
            "FechaFin": date_to,
            "Capacidad": data["Capacidad"]
        })

        term_id = rep.create(term)

        school_term = date_from.split("-")[0] + "-" + date_to.split("-")[0]
        AuditoriaRep().create(Auditoria({
            "Usuario": Usuario({
                "id": payload["id"]
            }),
            "Accion": "Registro",
            "Descripcion": f"Establecido período escolar {school_term}"
        }))

        return jsonify({"id": term_id})
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@school_term_bp.route("/school_term/get", methods=["GET"])
@school_term_bp.route("/school_term/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        term: PeriodoEscolar
        if id:
            payload = Security.verify_token(request.headers)

            if not payload or payload["role"] != Rol.ADMIN.name:
                raise Unauthorized()
            elif not Validations.is_uuid(id):
                raise InvalidId(f"ID inválido: {id}")

            term = rep.get(id)
        else:
            term = rep.get_latest()
        return jsonify(term.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@school_term_bp.route("/school_term/list", methods=["GET"])
def list():
    try:
        offset = None
        limit = None

        if request.args.get("offset") != None:
            offset = int(request.args.get("offset"))
        if request.args.get("limit") != None:
            limit = int(request.args.get("limit"))

        terms = rep.list(limit, offset)
        return jsonify([t.to_dict() for t in terms]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@school_term_bp.route("/school_term/update", methods=["PUT"])
def update():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data:
            raise MissingEntityData("No se recibieron datos")
        elif not "PeriodoEscolarId" in data:
            raise MissingEntityData("Debes especificar el identificador del período escolar")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("El identificador del período escolar es inválido")
        elif not "FechaInicio" in data and not "FechaFin" in data:
            raise MissingEntityData("Faltan la fecha de inicio o la fecha del fin del período escolar")
        elif not Validations.is_date(data["FechaInicio"]):
            raise ValidationError("La fecha de inicio del período escolar tiene un formato inválido")
        elif not Validations.is_date(data["FechaFin"]):
            raise ValidationError("La fecha fin del período escolar tiene un formato inválido")
        
        rep.update(PeriodoEscolar({
            "id": data["PeriodoEscolarId"],
            "FechaInicio": data["FechaInicio"],
            "FechaFin": data["FechaFin"],
            "Capacidad": data["Capacidad"]
        }));

        AuditoriaRep().create(Auditoria({
            "Accion": "Actualizar",
            "Descripcion": "Datos del periód escolar actualizados",
            "Usuario": Usuario({
                "id": payload["id"]
            })
        }))
    
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@school_term_bp.route("/school_term/get_all", methods=["GET"])
def get_all():
    try:
        terms = rep.get_all()
        return jsonify([t.to_dict() for t in terms]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
