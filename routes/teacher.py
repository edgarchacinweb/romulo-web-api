from flask import Blueprint, jsonify, request, Response
from database.Docente import DocenteRep
from models.Docente import Docente
from models.DatosPersona import DatosPersona
from models.Materia import Materia
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from models.Usuario import Usuario, Rol
from models.Auditoria import Auditoria
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep

rep = DocenteRep()
logger = Logger()
auditory = AuditoriaRep()

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/teacher/count", methods=["GET"])
def count():
    try:
        count = rep.count()
        return jsonify({"count": count}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
