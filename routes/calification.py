from flask import Blueprint, jsonify, request, Response
from database.Nota import NotaRep
from models.Nota import Nota
from models.Usuario import Rol
from models.Boleta import Boleta
from models.Materia import Materia
from utils.exceptions import *
from utils.validations import Validations
from utils.Security import Security
from utils.logger import Logger
from utils.handler import  exception_handler

rep = NotaRep()
logger = Logger()

blueprint = Blueprint("calification", __name__)

@blueprint.route("/calification/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not any(key in data for key in ("Ponderacion", "Lapso", "MateriaId", "BoletaId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_qualification(data["Ponderacion"]):
            raise ValidationError("La ponderación introducida es inválida.")
        elif not Validations.is_lapse(data["Lapso"]):
            raise ValidationError("El lapso introducido es inválido.")
        elif not Validations.is_uuid(data["MateriaId"]):
            raise InvalidId("El ID de la materia es inválido.")
        elif not Validations.is_uuid(data["BoletaId"]):
            raise InvalidId("El ID de la boleta es inválido.")

        calification = Nota({
            "Ponderacion": data["Ponderacion"],
            "Lapso": data["Lapso"],
            "Materia": Materia({"id": data["MateriaId"]}),
            "Boleta": Boleta({"id": data["BoletaId"]})
        })

        if rep.already_exists(calification.materia.id, calification.lapso, calification.boleta.id):
            raise EntityAlreadyExists("Ya existe una calificación para esta materia en este lapso.")
        
        id = rep.create(calification)
        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    

@blueprint.route("/calification/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID invático: {id}")

        data = rep.get(id)

        if data == None:
            raise EntityNotFound(f"No se encontró la calificación.")

        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    

@blueprint.route("/calification/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        data = rep.delete(id)

        if data == None:
            raise EntityNotFound(f"No se encontró la calificación para eliminarse.")

        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/calification/update/<string:id>", methods=["PUT"])
def update(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not any(key in data for key in ("Ponderacion", "Lapso", "MateriaId", "BoletaId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_qualification(data["Ponderacion"]):
            raise ValidationError("La ponderación introducida es inválida.")
        elif not Validations.is_lapse(data["Lapso"]):
            raise ValidationError("El lapso introducido es inválido.")
        elif not Validations.is_uuid(data["MateriaId"]):
            raise InvalidId("El ID de la materia es inválido.")
        elif not Validations.is_uuid(data["BoletaId"]):
            raise InvalidId("El ID de la boleta es inválido.")

        calification = Nota({
            "id": id,
            "Ponderacion": data["Ponderacion"],
            "Lapso": data["Lapso"],
            "Materia": Materia({"id": data["MateriaId"]}),
            "Boleta": Boleta({"id": data["BoletaId"]})
        })

        affected = rep.update(calification)

        if not affected:
            raise EntityNotFound(f"No se encontró la calificación para actualizar.")

        return jsonify({"id": id}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/calification/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        limit = None
        offset = None

        if "limit" in request.args:
            limit = int(request.args["limit"])
        if "offset" in request.args:
            offset = int(request.args["offset"])

        data = rep.list(limit, offset)

        if data == None:
            raise EntityNotFound(f"No se encontró la calificación.")

        return jsonify([calification.to_dict() for calification in data]), 200
    except ValueError:
        return jsonify({"message": "Debes introducir valores numéricos"}), 400
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/calification/list/by_student", methods=["GET"])
def list_by_student():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()
        
        if not any(key in request.args for key in ("Grado", "EstudianteId")):
            raise MissingEntityData("Debes introducir el grado y el id del estudiante")
        
        if not Validations.is_grade(request.args["Grado"]):
            raise ValidationError("El grado introducido es inválido.")
        elif not Validations.is_uuid(request.args["EstudianteId"]):
            raise InvalidId("El ID del estudiante es inválido.")

        grade: int = int(request.args["Grado"])
        student_id: str = request.args["EstudianteId"]

        data = rep.list_by_student_and_grade(grade, student_id)

        return jsonify([calification.to_dict() for calification in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
