from flask import Blueprint, request, jsonify, Response
from models.PeriodoEscolar import PeriodoEscolar
from database.PeriodoEscolar import PeriodoEscolarRep
from models.Usuario import Usuario, Rol
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.exceptions import *
from utils.handler import exception_handler
from database.Auditoria import Auditoria, AuditoriaRep
from database.connection import Connection
from datetime import datetime

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

        # --- NUEVAS VALIDACIONES DE REGLAS DE NEGOCIO ---
        try:
            dt_inicio = datetime.strptime(date_from, "%Y-%m-%d")
            dt_fin = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Formato de fecha inválido, se espera YYYY-MM-DD")

        # 1. Validar inicio inamovible
        if dt_inicio.month != 9 or dt_inicio.day != 16:
            raise ValidationError("La fecha de inicio siempre debe ser el 16 de septiembre del año correspondiente.")
        
        # 2. Validar fin inamovible
        if dt_fin.month != 7 or dt_fin.day != 31:
            raise ValidationError("La fecha de fin siempre debe ser el 31 de julio del año correspondiente.")
            
        # 3. Validar que la duración sea exactamente un ciclo (1 año de diferencia)
        if dt_fin.year != dt_inicio.year + 1:
            raise ValidationError("El período escolar debe durar exactamente un ciclo (el año de finalización debe ser el consecutivo al de inicio).")
        # ------------------------------------------------

        term = PeriodoEscolar({
            "FechaInicio": date_from,
            "FechaFin": date_to,
            "Capacidad": data["Capacidad"]
        })

        latest_school_term = rep.get_latest()

        if latest_school_term is not None and latest_school_term.fecha_inicio == term.fecha_inicio and latest_school_term.fecha_fin == term.fecha_fin:
            return Response(status=409)

        term_id = rep.create(term)

        school_term = date_from.split("-")[0] + "-" + date_to.split("-")[0]
        AuditoriaRep().create(Auditoria({
            "Usuario": Usuario({
                "id": payload["id"]
            }),
            "Accion": "Registro",
            "Descripcion": f"Establecido período escolar {school_term}"
        }))

        return jsonify({"id": term_id}), 201
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
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM "PeriodoEscolar" ORDER BY "FechaInicio" DESC
            """
        )

        terms = cursor.fetchall()

        if not terms:
            terms = []

        return jsonify([{
            "PeriodoEscolarId": t[0],
            "FechaInicio": t[1],
            "FechaFin": t[2]
        } for t in terms]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

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
        
        # --- NUEVAS VALIDACIONES DE REGLAS DE NEGOCIO PARA ACTUALIZACIÓN ---
        date_from = data["FechaInicio"]
        date_to = data["FechaFin"]

        try:
            dt_inicio = datetime.strptime(date_from, "%Y-%m-%d")
            dt_fin = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Formato de fecha inválido, se espera YYYY-MM-DD")

        if dt_inicio.month != 9 or dt_inicio.day != 16:
            raise ValidationError("La fecha de inicio siempre debe ser el 16 de septiembre del año correspondiente.")
        
        if dt_fin.month != 7 or dt_fin.day != 31:
            raise ValidationError("La fecha de fin siempre debe ser el 31 de julio del año correspondiente.")
            
        if dt_fin.year != dt_inicio.year + 1:
            raise ValidationError("El período escolar debe durar exactamente un ciclo (el año de finalización debe ser el consecutivo al de inicio).")
        # -------------------------------------------------------------------

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