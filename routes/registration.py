from flask import Blueprint, jsonify, request, Response
from database.PeriodoInscripcion import PeriodoInscripcionRep
from database.PeriodoEscolar import PeriodoEscolarRep
from models.Usuario import Rol
from models.PeriodoInscripcion import PeriodoInscripcion
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from datetime import datetime
from utils.handler import exception_handler
from database.Auditoria import Auditoria, AuditoriaRep
from database.connection import Connection  # <--- Importación necesaria

rep = PeriodoInscripcionRep()
escolar_rep = PeriodoEscolarRep()
logger = Logger()

reg_term_bp = Blueprint("registration_term", __name__)

@reg_term_bp.route("/registration/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()
        logger.info(data)

        if not data or (not any(key in data for key in ("FechaInicio", "FechaFin"))):
            raise MissingEntityData("No se recibieron datos")
        if not "FechaInicio" in data or not "FechaFin" in data:
            raise MissingEntityData("Faltan datos para realizar la operación")
        elif not Validations.is_date(data["FechaInicio"]) or not Validations.is_date(data["FechaFin"]):
            raise ValidationError("Los formatos de las fechas son inválidos (YYYY-MM-DD)")
        
        # --- CORRECCIÓN DE REGLA DE NEGOCIO ---
        # En vez de obtener el "último registrado" obtenemos el "actual en curso"
        all_terms = escolar_rep.get_all()
        now = datetime.now()
        
        # En Python, Agosto es el mes 8.
        target_start_year = now.year if now.month >= 8 else now.year - 1
        
        registration_term = None
        if all_terms:
            for term in all_terms:
                # Extraemos el año de inicio (puede ser object Date o String dependiendo de BD)
                term_year = int(str(term.fecha_inicio).split("-")[0])
                if term_year == target_start_year:
                    registration_term = term
                    break
        
        if not registration_term:
            raise ValidationError(f"No existe un período escolar activo registrado para el ciclo {target_start_year}-{target_start_year+1}. Debes crearlo primero.")
        # -------------------------------------

        format = "%Y-%m-%d"
        date_dict = {
            "Inicio": datetime.strptime(data["FechaInicio"], format).date(),
            "Fin": datetime.strptime(data["FechaFin"], format).date(),
            "PeriodoEscolar": registration_term
        }
        reg = PeriodoInscripcion(date_dict)
        reg_id = rep.create(reg)

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": "Período de inscripción creado"
        }))

        return jsonify({"id": reg_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@reg_term_bp.route("/registration/get", methods=["GET"])
@reg_term_bp.route("/registration/get/<string:id>", methods=["GET"])
def get(id=None):
    try:
        if not id:
            entity = rep.get_latest()
        else:
            payload = Security.verify_token(request.headers)

            if not payload or payload["role"] != Rol.ADMIN.name:
                raise Unauthorized()
            elif not Validations.is_uuid(id):
                raise InvalidId(f"Invalid \"Inscripcion\" ID: {id}")
            entity = rep.get(id)
        return jsonify(entity.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@reg_term_bp.route("/registration/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        offset = request.args.get("offset")
        limit = request.args.get("limit")
        if offset != None:
            offset = int(offset)
        if limit != None:
            limit = int(limit)

        data = rep.list()

        if data == None or len(data) == 0:
            raise EntityNotFound("No hay inscripciones disponibles")
        
        return jsonify([d.to_dict() for d in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@reg_term_bp.route("/registration/update", methods=["PATCH"])
def update():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not data or not any(key in data for key in ("PeriodoInscripcionId", "FechaInicio", "FechaFin")):
            raise MissingEntityData("No se recibieron datos")
        elif not any(key in data for key in ("FechaInicio", "FechaFin")):
            raise MissingEntityData("Faltan datos para realizar la operación")
        elif "Inicio" in data and not Validations.is_date(data["FechaInicio"]):
            raise ValidationError("El formato de la fecha de inicio es inválido (YYYY-MM-DD)")
        elif "Fin" in data and not Validations.is_date(data["FechaFin"]):
            raise ValidationError("El formato de la fecha de fin es inválido (YYYY-MM-DD)")
        elif not Validations.is_uuid(data["PeriodoInscripcionId"]):
            raise InvalidId("El ID es inválido")
        
        format = "%Y-%m-%d"
        date_dict = {
            "id": data["PeriodoInscripcionId"],
        }
        if "FechaInicio" in data: date_dict["Inicio"] = datetime.strptime(data["FechaInicio"], format).date()
        if "FechaFin" in data: date_dict["Fin"] = datetime.strptime(data["FechaFin"], format).date()
        reg = PeriodoInscripcion(date_dict)
        affected = rep.update(reg)
        if not affected:
            raise EntityUpdateError("Ocurrio un error en la base de datos")
        
        AuditoriaRep().create(Auditoria({
            "Accion": "Acualización",
            "Descripcion": "Período de inscripción actualizado"
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@reg_term_bp.route("/registration/close/<string:id>", methods=["PATCH"])
def close_registration(id):
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        if not Validations.is_uuid(id):
            raise InvalidId("El ID es inválido")

        connection = Connection().get_connection()
        cursor = connection.cursor()

        # Verificar si la fecha de fin ya pasó (período ya cerrado definitivamente)
        cursor.execute(
            'SELECT "Fin", "Activo" FROM "PeriodoInscripcion" WHERE "PeriodoInscripcion" = %s',
            (id,)
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            raise EntityNotFound("No se encontró el período de inscripción")

        fecha_fin, activo = row[0], row[1]
        hoy = datetime.now().date()

        if hoy > fecha_fin:
            cursor.close()
            # El período ya expiró automáticamente; no se requiere acción manual
            return (
                jsonify({"message": "Este período ya está cerrado definitivamente por vencimiento de fecha."}),
                409,
            )

        sql = 'UPDATE "PeriodoInscripcion" SET "Activo" = FALSE WHERE "PeriodoInscripcion" = %s'
        cursor.execute(sql, (id,))
        affected = cursor.rowcount

        if affected == 0:
            connection.rollback()
            cursor.close()
            raise EntityNotFound("No se encontró el período de inscripción o ya está cerrado")

        connection.commit()
        cursor.close()

        AuditoriaRep().create(Auditoria({
            "Accion": "Actualización",
            "Descripcion": "Período de inscripción cerrado manualmente"
        }))

        return jsonify({"message": "Período cerrado exitosamente"}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]


@reg_term_bp.route("/registration/reactivate/<string:id>", methods=["PATCH"])
def reactivate_registration(id):
    """
    Reactiva un período de inscripción cerrado manualmente, SOLO si su Fecha de Fin
    no ha vencido auún. Si el día actual es mayor a Fin, se rechaza con HTTP 403
    sin importar qué envíe el cliente.
    """
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        if not Validations.is_uuid(id):
            raise InvalidId("El ID es inválido")

        connection = Connection().get_connection()
        cursor = connection.cursor()

        # Consultar la fecha de fin directamente en BD (fuente de verdad, no el cliente)
        cursor.execute(
            'SELECT "Fin", "Activo" FROM "PeriodoInscripcion" WHERE "PeriodoInscripcion" = %s',
            (id,)
        )
        row = cursor.fetchone()

        if not row:
            cursor.close()
            raise EntityNotFound("No se encontró el período de inscripción")

        fecha_fin, activo = row[0], row[1]

        # VALIDACIÓN CRÍTICA DE SEGURIDAD:
        # Usamos datetime.now().date() (hora del servidor) vs fecha_fin (objeto date de PG).
        # Ambos son objetos Python `date`, sin strings ni timezones involucrados.
        hoy = datetime.now().date()

        if hoy > fecha_fin:
            cursor.close()
            return (
                jsonify({
                    "message": "No se puede reactivar: la Fecha de Fin de este período ya venció. "
                               "El cierre es definitivo e irreversible."
                }),
                403,
            )

        if activo:
            cursor.close()
            return jsonify({"message": "El período ya está activo."}), 200

        cursor.execute(
            'UPDATE "PeriodoInscripcion" SET "Activo" = TRUE WHERE "PeriodoInscripcion" = %s',
            (id,)
        )
        affected = cursor.rowcount

        if affected == 0:
            connection.rollback()
            cursor.close()
            raise EntityNotFound("No se pudo reactivar el período")

        connection.commit()
        cursor.close()

        AuditoriaRep().create(Auditoria({
            "Accion": "Actualización",
            "Descripcion": "Período de inscripción reactivado por el administrador"
        }))

        return jsonify({"message": "Período reactivado exitosamente"}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

# --- Rutas de Conteo para el Dashboard ---

@reg_term_bp.route("/registration/count/students", methods=["GET"])
def countTotalStudents():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        cursor.execute('SELECT COUNT(*) FROM "Estudiante";')
        total = cursor.fetchone()[0]
        return jsonify({"count": total}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@reg_term_bp.route("/registration/count/teachers", methods=["GET"])
def countTotalTeachers():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        cursor.execute('SELECT COUNT(*) FROM "Usuario" WHERE "Rol" = \'docente\';')
        total = cursor.fetchone()[0]
        return jsonify({"count": total}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@reg_term_bp.route("/registration/count", methods=["GET"])
def registrationCount():
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        cursor.execute('SELECT COUNT(*) FROM "EstadoEstudiante" WHERE "Estado" = \'revision\';')
        total = cursor.fetchone()[0]
        
        return jsonify({"count": total}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()