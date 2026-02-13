from flask import Blueprint, request, jsonify, Response
from utils.logger import Logger
from utils.handler import exception_handler
from utils.exceptions import * 
from utils.validations import Validations
from utils.Security import Security
from database.connection import Connection

schedule_bp = Blueprint("schedule", __name__)
logger = Logger()

@schedule_bp.route("/schedule/filter", methods=["POST"])
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

        cursor.execute("""
            SELECT * FROM "Horario" AS h
            INNER JOIN "BloqueHorario" AS bh ON bh."BloqueHorarioId"=h."BloqueHorarioId"
            WHERE h."CursoId"=%s AND h."Seccion"=%s AND h."PeriodoEscolarId"=%s
            ORDER BY bh."HoraInicio" ASC;
        
        """, (data["CursoId"], data["Seccion"], data["PeriodoEscolarId"]) );

        rows = cursor.fetchall()

        return jsonify([{
            "HorarioId": h[0],
            "Dia": h[1],
            "DocenteId": h[2],
            "MateriaId": h[3],
            "BloqueHorarioId": h[4],
            "CursoId": h[5],
            "PeriodoEscolarId": h[6],
            "Seccion": h[7],
            "Receso": h[8]
        } for h in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@schedule_bp.route("/schedule/blocks", methods=["GET"])
def blocks():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        cursor.execute("SELECT * FROM \"BloqueHorario\";")
        rows = cursor.fetchall()

        return jsonify([{
    "BloqueHorarioId": bh[0],
    "HoraInicio": bh[1].strftime("%H:%M") if bh[1] else None,
    "HoraFin": bh[2].strftime("%H:%M") if bh[2] else None
} for bh in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
