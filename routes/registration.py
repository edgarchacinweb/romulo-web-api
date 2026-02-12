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
from database.connection import Connection # Importación vital

rep = PeriodoInscripcionRep()
escolar_rep = PeriodoEscolarRep()
logger = Logger()

reg_term_bp = Blueprint("registration_term", __name__)

# ... (Tus rutas de create, get, list y update se mantienen igual) ...

@reg_term_bp.route("/registration/count/students", methods=["GET"])
def countTotalStudents():
    """Ruta para el recuadro de Total Estudiantes"""
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        # Cuenta limpia de todos los estudiantes registrados
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
    """Ruta para el recuadro de Total Docentes"""
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        # Cuenta de usuarios con rol docente
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
    """Ruta para el recuadro de Inscripciones (Pendientes por revisar)"""
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        # Contamos solo los que están en revisión
        cursor.execute('SELECT COUNT(*) FROM "EstadoEstudiante" WHERE "Estado" = \'revision\';')
        total = cursor.fetchone()[0]
        
        return jsonify({"count": total}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()