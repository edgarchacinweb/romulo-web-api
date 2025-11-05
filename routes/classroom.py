from flask import Blueprint, jsonify, request, Response
from database.Clase import Clase, ClaseRep
from database.Auditoria import AuditoriaRep, Auditoria
from models.Usuario import Rol, Usuario
from models.Docente import Docente
from models.Curso import Curso
from models.PeriodoEscolar import PeriodoEscolar
from utils.exceptions import *
from utils.validations import Validations
from utils.Security import Security
from utils.logger import Logger
from utils.handler import  exception_handler

class_bp = Blueprint("class", __name__)
logger = Logger()
rep = ClaseRep()

@class_bp.route("/class/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not any(key in data for key in ("DocenteId", "CursoId", "PeriodoEscolarId", "Seccion")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_uuid(data["DocenteId"]):
            raise InvalidId("El ID del docente es inválido.")
        if not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")
        if not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("El ID del periodo escolar es inválido.")
        if not Validations.is_section(data["Seccion"]):
            raise ValidationError("La sección introducida es inválida.")

        id = rep.create(Clase({
            "Docente": Docente({
                "id": data["DocenteId"]
            }),
            "Curso": Curso({
                "id": data["CursoId"]
            }),
            "PeriodoEscolar": PeriodoEscolar({
                "id": data["PeriodoEscolarId"]
            }),
            "Seccion": data["Seccion"]
        }))

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": "Clase impartida registrada",
            "Usuario": Usuario({"id": payload["id"] })
        }))
        
        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@class_bp.route("/class/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId("El identificador de la clase impartida es inválido")
        
        data = rep.get(id)
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@class_bp.route("/class/filter", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        filters = Clase({})

        if "DocenteId" in request.args:
            filters.docente = Docente({"id": request.args.get("DocenteId")})
        if "CursoId" in request.args:
            filters.Curso = Curso({"id": request.args.get("CursoId")})
        if "PeriodoEscolarId" in request.args:
            filters.periodo_escolar = PeriodoEscolar({"id": request.args.get("PeriodoEscolarId")})
        if "Seccion" in request.args:
            filters.seccion = request.args.get("Seccion")

        results = rep.filter(filters)

        return jsonify([d.to_dict() for d in results]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
