from flask import Blueprint, jsonify, request, Response
from database.Boleta import BoletaRep
from models.Boleta import Boleta
from models.Curso import Curso
from models.Estudiante import Estudiante
from models.Usuario import Rol
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.handler import exception_handler

rep = BoletaRep()
logger = Logger()

blueprint = Blueprint("report-card", __name__)

@blueprint.route("/report-card/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload and not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            Unauthorized()

        data = request.get_json()

        if not data:
            raise MissingEntityData("No se recibieron datos")
        elif not any(key in data for key in ("EstudianteId", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_uuid(data["EstudianteId"]):
            raise InvalidId("El ID del estudiante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        boleta = Boleta({
            "Estudiante": Estudiante({"id": data["EstudianteId"]}),
            "Curso": Curso({"id": data["CursoId"]})
        })
        id = rep.create(boleta)
        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@blueprint.route("/report-card/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID invático: {id}")

        report_card = rep.get(id)

        return jsonify(report_card.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/report-card/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        affected = rep.delete(id)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@blueprint.route("/report-card/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        limit = None
        offset = None

        if "limit" in request.args:
            limit = int(request.args.get("limit"))
        if "offset" in request.args:
            offset = int(request.args.get("offset"))

        data = rep.list(limit, offset)

        return jsonify([report_card.to_dict() for report_card in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
