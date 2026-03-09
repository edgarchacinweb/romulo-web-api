from utils.exceptions import MissingEntityData
from flask import Blueprint, jsonify, request, Response
from utils.exceptions import *
from utils.handler import exception_handler
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from database.connection import Connection
from models.Usuario import Rol

loadcalificationsterm_bp = Blueprint("loadcalificationsterm", __name__)

@loadcalificationsterm_bp.route("/load-calification-term/list", methods=["GET"])
def list():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]:
            raise Unauthorized()
    
        cursor.execute("""
        SELECT
            pcn."PeriodoCargaNotaId",
            pcn."FechaInicio",
            pcn."FechaFin",
            pcn."Activo",
            pcn."FechaCreacion",
            pe."PeriodoEscolarId",
            pe."FechaInicio",
            pe."FechaFin",
            l."LapsoId",
            l."Numero",
            l."FechaInicio",
            l."FechaFin"
        FROM
            "PeriodoCargaNota" AS pcn
        INNER JOIN "PeriodoEscolar" AS pe ON pe."PeriodoEscolarId"=pcn."PeriodoEscolarId"
        INNER JOIN "Lapso" AS l ON l."LapsoId"=pcn."LapsoId" ORDER BY pcn."FechaCreacion" DESC;
        """)
        rows = cursor.fetchall()

        if len(rows) == 0:
            return Response(status=404)
        return jsonify([{
            "PeriodoCargaNotaId": row[0],
            "FechaInicio": row[1].strftime("%Y-%m-%d"),
            "FechaFin": row[2].strftime("%Y-%m-%d"),
            "Activo": row[3],
            "FechaCreacion": row[4].strftime("%Y-%m-%d"),
            "PeriodoEscolar": {
                "PeriodoEscolarId": row[5],
                "FechaInicio": row[6].strftime("%Y-%m-%d"),
                "FechaFin": row[7].strftime("%Y-%m-%d")
            },
            "Lapso": {
                "LapsoId": row[8],
                "Numero": row[9],
                "FechaInicio": row[10].strftime("%Y-%m-%d"),
                "FechaFin": row[11].strftime("%Y-%m-%d")
            }
        } for row in rows]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@loadcalificationsterm_bp.route("/load-calification-term/save", methods=["POST"])
def save():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        code = 200
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]:
            raise Unauthorized()
    
        data = request.get_json()

        if not data["PeriodoEscolarId"]:
            raise MissingEntityData("Debes envíar el período escolar al que corresponse")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise ValueError("El período escolar debe ser un UUID")
        elif not data["LapsoId"]:
            raise MissingEntityData("Debes envíar el lapso al que corresponse")
        elif not Validations.is_uuid(data["LapsoId"]):
            raise ValueError("El lapso debe ser un UUID")
        elif not data["FechaInicio"]:
            raise MissingEntityData("Debes envíar la fecha de inicio")
        elif not Validations.is_valid_date(data["FechaInicio"]):
            raise ValueError("La fecha de inicio debe ser una fecha válida")
        elif not data["FechaFin"]:
            raise MissingEntityData("Debes envíar la fecha de fin")
        elif not Validations.is_valid_date(data["FechaFin"]):
            raise ValueError("La fecha de fin debe ser una fecha válida")

        # Si tiene ID debe actualizar, en caso contrario, crear nuevo registro
        if data.get("PeriodoCargaNotaId"):
            cursor.execute("""
            UPDATE "PeriodoCargaNota"
            SET "FechaInicio" = %s, "FechaFin" = %s, "PeriodoEscolarId" = %s, "LapsoId" = %s
            WHERE "PeriodoCargaNotaId" = %s
            """, (data["FechaInicio"], data["FechaFin"], data["PeriodoEscolarId"], data["LapsoId"], data["PeriodoCargaNotaId"]))
            conn.commit()
            return jsonify({"PeriodoCargaNotaId": data["PeriodoCargaNotaId"]}), code
        else:
            code = 201

            # Desactivar todos los periodos anteriores
            cursor.execute("""
            UPDATE "PeriodoCargaNota" SET "Activo"=false WHERE "PeriodoEscolarId"=%s AND "LapsoId"=%s
            """, (data["PeriodoEscolarId"], data["LapsoId"]))

            #Insertar nuevo registro
            cursor.execute("""
            INSERT INTO "PeriodoCargaNota" ("FechaInicio", "FechaFin", "PeriodoEscolarId", "LapsoId")
            VALUES (%s, %s, %s, %s) RETURNING "PeriodoCargaNotaId";
            """, (data["FechaInicio"], data["FechaFin"], data["PeriodoEscolarId"], data["LapsoId"]))
            id = cursor.fetchone()
            conn.commit()
            return jsonify({"PeriodoCargaNotaId": id[0]}), code

    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
