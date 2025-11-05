from flask import Blueprint, request, jsonify, Response
from models.Usuario import Rol
from models.HorarioItem import HorarioItem
from models.Docente import Docente
from models.Horario import Horario
from models.Auditoria import Auditoria
from models.BloqueHorario import BloqueHorario
from database.HorarioItem import HorarioItemRep
from utils.logger import Logger
from utils.exceptions import *
from utils.Security import Security
from utils.validations import Validations
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from typing import List

schedule_item_bp = Blueprint("schedule_item", __name__)

logger = Logger()
rep = HorarioItemRep()
auditory = AuditoriaRep()

@schedule_item_bp.route("/schedule/add", methods=["POST"])
def create_schedule():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("No autorizado")
        
        data = request.get_json()

        if not data:
            raise ValidationError("No se recibieron datos")
        elif any(key not in data for key in ("HoraInicio", "HoraFin", "Dia", "HorarioId")):
            raise ValidationError("Faltan datos para realizar la operación")
        elif not "DocenteId" in data and not "Actividad" in data:
            raise ValidationError("Debes especificar el docente que impartira la materio o la actividad a realizar")
        elif not Validations.is_uuid(data["HorarioId"]):
            raise ValidationError("El identificador del horario es inválido")
        elif "DocenteId" in data and not Validations.is_uuid(data["DocenteId"]):
            raise ValidationError("El id del docente no es válido")
        elif "Actividad" in data and not Validations.is_activity(data["Actividad"]):
            raise ValidationError("El nombre de la actividad tiene un formato inválido")

        schedule = HorarioItem({
            "HoraInicio": data["HoraInicio"],
            "HoraFin": data["HoraFin"],
            "Dia": data["Dia"],
            "Horario": Horario({
                "id": data["HorarioId"]
            }),
        })

        if "DocenteId" in data:
            schedule.Docente = Docente({"id": data["DocenteId"]})
        else:
            schedule.Actividad = data["Actividad"]

        schedule_id = rep.create(schedule)
        return jsonify({"id": schedule_id}), 201

    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@schedule_item_bp.route("/schedule/create/row", methods=["POST"])
def create_schedule_row():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("No autorizado")
        
        data = request.get_json()

        if not data:
            raise ValidationError("No se recibieron datos")
        # elif any(key not in data for key in ("HoraInicio", "HoraFin", "Tipo", "HorarioId")):
        #     raise ValidationError("Faltan datos para realizar la operación")
        # elif not Validations.is_uuid(data["HorarioId"]):
        #     raise ValidationError("El identificador del horario es inválido")
        
        rows = list()

        for i in range(5):
            s = HorarioItem({
                "HoraInicio": data[i]["HoraInicio"],
                "HoraFin": data[i]["HoraFin"],
                "Dia": data[i]["Dia"],
                "Horario": Horario({
                    "id": data[i]["HorarioId"]
                }),
            })

            if data[i]["Tipo"] == "subject":
                s.Docente = Docente({"id": data[i]["DocenteId"]})
            else:
                s.Actividad = data[i]["Actividad"]

            rows.append(s)

        result = rep.create_row(rows)

        if not result:
            raise ValidationError("No se pudo crear el horario")

        auditory.create(Auditoria({
            "Acccion": "Registro",
            "Descripcion": "Creada fila de horario"
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_item_bp.route("/schedule/get/<string:id>", methods=["GET"])
@schedule_item_bp.route("/schedule/get/all/<string:id>")
def get_schedule(id: str = ""):
    try:
        if not Validations.is_uuid(id):
            raise InvalidId("El identificador de la fila del horario es incorrecto")
        if "/get/all" in request.url:
            schedule = rep.get_all(id)
            schedules = dict()
            
            for s in schedule:
                logger.debug(s.to_dict())
                if not s.Dia.value in schedules: schedules[s.Dia.value] = []
                schedules[s.Dia.value] += [s.to_dict()]
            
            return jsonify({"data": schedules, "rows": len(schedule) / 5 }), 200
        else:
            schedule_row = rep.get(id)
            return jsonify(schedule_row.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@schedule_item_bp.route("/schedule/update/<string:id>", methods=["PATCH"])
def update(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("No autorizado")
        
        if not Validations.is_uuid(id):
            raise ValidationError("El id del horario no es válido")
        
        data = request.get_json()

        if type(data) is not list or len(data) == 0:
            raise ValidationError("Debes enviar una lista con los elementos del horario actualizado")
        
        for d in data:
            if not Validations.is_uuid(d["HorarioId"]):
                raise InvalidId("ID del horario inválido")
            
            rep.update(HorarioItem({
                "id": d["HorarioItemId"],
                "Dia": d["Dia"],
                "BloqueHorario": BloqueHorario({
                    "id": d["BloqueHorarioId"]
                }),
                "Docente": Docente({
                    "id": d["DocenteId"]
                }),
                "Horario": Horario({
                    "id": d["HorarioId"]
                }),
                "Actividad": d["Actividad"]
            }))
        
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@schedule_item_bp.route("/schedule/delete/<string:id>", methods=["DELETE"])
@schedule_item_bp.route("/schedule/delete/row/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        if not Validations.is_uuid(id):
            raise ValidationError("El id del horario no es válido")
        
        if "row" in request.base_url:
            data = request.get_json()

            if not data:
                raise ValidationError("No se recibieron datos")
            elif not id:
                raise ValidationError("Debes especificar el identificador del horario")
            elif not Validations.is_uuid(id):
                raise ValidationError("El identificador del horario es inválido")
            elif not "HoraInicio" in data or not "HoraFin" in data:
                raise ValidationError("Faltan datos para realizar la operación")
            elif not Validations.is_time(data["HoraInicio"]) or not Validations.is_time(data["HoraFin"]):
                raise ValidationError("Los horarios tienen un formato inválido")
            
            deleted = rep.delete_row(id, data["HoraInicio"], data["HoraFin"])
        else:
            deleted = rep.delete(id)

        if not deleted:
            raise EntityDeleteError("No se pudo realizar la operación")
        
        auditory.create(Auditoria({
            "Acccion": "Eliminación",
            "Descripcion": "Deshabilitada fila de horario"
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
