from flask import Blueprint, request, jsonify, Response
from utils.logger import Logger
from utils.handler import exception_handler
from utils.exceptions import * 
from utils.validations import Validations
from utils.Security import Security
from database.connection import Connection

schedule_bp = Blueprint("schedule", __name__)
logger = Logger()

@schedule_bp.route("/schedule/filter", methods=["GET"])
def filter():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        data = request.get_json()
        
        if "CursoId" not in data or not data["CursoId"]:
            raise MissingEntityData("Debe especificar el grado")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El identificador del grado es inválido")
        elif "Seccion" not in data or not data["Seccion"]:
            raise MissingEntityData("Debe especificar la sección")
        elif not Validations.is_section(data["Seccion"]):
            raise InvalidId("Debes indicar una sección válida ")
        elif "PeriodoEscolarId" not in data or not data["PeriodoEscolarId"]:
            raise MissingEntityData("Debe especificar el período escolar")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("El identificador del período escolar es inválido")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

