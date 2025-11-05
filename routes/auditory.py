from flask import Blueprint, jsonify, request, Response
from utils.handler import exception_handler
from utils.Security import Security
from utils.logger import Logger
from models.Usuario import Usuario, Rol
from models.Auditoria import Auditoria
from utils.exceptions import Unauthorized
from database.Auditoria import AuditoriaRep
from utils.validations import Validations
from utils.exceptions import ValidationError

logger = Logger()
rep = AuditoriaRep()

auditory_bp = Blueprint("auditory", __name__)

@auditory_bp.route("/auditory/filter", methods=["GET"])
def get_auditory():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        filters: Auditoria = Auditoria({
            "Accion": request.args.get("Accion") or None
        })

        if "Rol" in request.args:
            filters.usuario = Usuario({
                "Rol": Rol(request.args.get("Rol"))
            })

        date_from = request.args.get("from") or None
        date_to = request.args.get("to") or None

        if date_from and not Validations.is_date(date_from):
            raise ValidationError("La fecha de inicio tiene un formato inválido")
        if date_to and not Validations.is_date(date_to):
            raise ValidationError("La fecha de fin tiene un formato inválido")
        
        results = rep.filter(filters, date_from, date_to)

        return jsonify([d.to_dict() for d in results]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
