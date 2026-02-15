from flask import Blueprint, jsonify, request, Response
from models.Usuario import Rol
from models.Auditoria import Auditoria
from models.Usuario import Usuario
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from database.connection import Connection

logger = Logger()
auditory = AuditoriaRep()

subject_bp = Blueprint("subject", __name__)

subject_bp.route("/subject/list", methods=["GET"])
def list_subjects():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        cursor = Connection().get_connection().cursor()
        cursor.execute("SELECT * FROM \"Materia\" WHERE \"Activo\" = true;")
        rows = cursor.fetchall()

        return jsonify([{
            "MateriaId": s[0],
            "Nivel": s[1],
            "Nombre": s[2]
        } for s in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
