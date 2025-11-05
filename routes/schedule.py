from flask import Blueprint, request, jsonify, Response
from models.PeriodoEscolar import PeriodoEscolar
from models.Usuario import Rol
from models.Curso import Curso
from models.Horario import Horario
from models.Auditoria import Auditoria
from database.Horario import HorarioRep
from utils.logger import Logger
from utils.exceptions import *
from utils.Security import Security
from utils.validations import Validations
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from database.BloqueHorario import BloqueHorarioRep, BloqueHorario
from database.HorarioItem import HorarioItemRep
from models.HorarioItem import Dia, HorarioItem
from datetime import datetime, date
from typing import List

schedule_bp = Blueprint("schedule", __name__)

logger = Logger()
rep = HorarioRep()
auditory = AuditoriaRep()
schedule_block = BloqueHorarioRep()
horario_item = HorarioItemRep()

@schedule_bp.route("/schedule/get/info/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        if not Validations.is_uuid(id):
            raise ValidationError("El identificador del horario es inválido")

        schedule = rep.get(id)

        return jsonify(schedule), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_bp.route("/schedule/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        limit = 10
        offset = 0

        if "limit" in request.args:
            limit = int(request.args.get("limit"))
        if "offset" in request.args:
            offset = int(request.args.get("offset"))

        schedules = rep.list(limit, offset)

        return jsonify({"resultados": [s.to_dict() for s in schedules], "total": len(schedules)}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_bp.route("/schedule/get_all", methods=["GET"])
@schedule_bp.route("/schedule/get_all/<string:school_term>", methods=["GET"])
def get_all(school_term: str = ""):
    try:
        if school_term and not Validations.is_uuid(school_term):
            raise ValidationError("El identificador del curso académico es inválido")

        if not school_term:
            schedules = rep.get_all()
        else:
            schedules = rep.get_all_by_school_term(school_term)

        logger.debug(schedules)
        return jsonify(schedules), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_bp.route("/schedule/list/teachers/<string:id>", methods=["GET"])
def list_teachers(id: str = ""):
    try:
        if not Validations.is_uuid(id):
            raise ValidationError("El identificador del curso académico es inválido")

        teachers = rep.list_by_schedule(id)

        return jsonify([t.to_dict() for t in teachers]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_bp.route("/schedule/filter", methods=["GET"])
def filter():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        school_term = request.args.get("periodo_escolar_id")
        course = request.args.get("curso_id")
        section = request.args.get("seccion")

        if not school_term:
            raise ValidationError("Debes especificar el período escolar")
        elif school_term and not Validations.is_uuid(school_term):
            raise ValidationError("El identificador del curso académico es inválido")
        elif course and not Validations.is_uuid(course):
            raise ValidationError("El identificador del curso académico es inválido")
        elif section and not Validations.is_section(section):
            raise ValidationError("La sección introducida es inválida.")

        schedules = rep.filter(Horario({
            "PeriodoEscolar": PeriodoEscolar({
                "id": school_term
            }),
            "Curso": Curso({
                "id": course
            }),
            "Seccion": section
        }))

        return jsonify([s.to_dict() for s in schedules]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_bp.route("/schedule/block/list", methods=["GET"])
def list_schedule_blocks():
    try:
        blocks = schedule_block.get_all()
        return [b.to_dict() for b in blocks]
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@schedule_bp.route("/schedule/data/get/<string:schedule_id>", methods=["GET"])
def get_schedule_data(schedule_id: str):
    try:
        if not Validations.is_uuid(schedule_id):
            raise InvalidId("El identificador del horario es inválido")
        
        data = horario_item.get_all(schedule_id)

        return jsonify([hi.to_dict() for hi in data])
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
