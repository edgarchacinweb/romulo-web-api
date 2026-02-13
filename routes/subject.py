from flask import Blueprint, jsonify, request, Response
from database.Materia import MateriaRep
from models.Materia import Materia
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

rep = MateriaRep()
logger = Logger()
auditory = AuditoriaRep()

subject_bp = Blueprint("subject", __name__)

@subject_bp.route("/subject/create", methods=["POST"])
def create_subject():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        subject = Materia(request.get_json())

        if not Validations.is_subject(subject.name):
            raise ValidationError("El nombre de la materia no es válido")

        subject_id = rep.create(subject)
        
        if not subject_id:
            raise InsertEntityError("Ocurrido un error al intentar registrar la materia")
        
        auditory.create(Auditoria({
            "Accion": "Registro",
            "Descripcion": f"Materia {subject.name} registrada",
            "Usuario": Usuario({
                "id": payload["id"],
            })
        }))

        return jsonify({"id": subject_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@subject_bp.route("/subject/get/<string:id>", methods=["GET"])
def get_subject(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        subject = rep.get(id)

        return jsonify(subject.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@subject_bp.route("/subject/list", methods=["GET"])
def list_subjects():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        cursor.execute("SELECT * FROM \"Materia\";")
        rows = cursor.fetchall()

        return jsonify([{
            "MateriaId": s[0],
            "Nombre": s[1]
        } for s in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@subject_bp.route("/subject/delete/<string:id>", methods=["DELETE"])
def delete_subject(id: str):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"Identificador de la materia inválido")

        subject = rep.get(id)
        rep.delete(id)

        auditory.create(Auditoria({
            "Accion": "Eliminación",
            "Descripcion": f"Materia {subject.name} eliminada",
            "Usuario": Usuario({
                "id": payload["id"],
            })
        }))

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@subject_bp.route("/subject/update", methods=["PUT"])
def update_subject():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not Validations.is_uuid(data["id"]):
            raise InvalidId(f"ID inválido")

        if not "Nombre" in data:
            raise MissingEntityData("No hay datos que actualizar")

        subject = Materia(data)
        affected = rep.update(subject)

        if not affected:
            raise EntityUpdateError("Ocurrido un error al intentar actualizar la materia")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@subject_bp.route("/subject/list/<int:grade>", methods=["GET"])
def list_subjects_by_grade(grade: int = 0):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_grade(str(grade)):
            raise ValidationError("El año académico introducido es inválido.")

        subjects = rep.list_by_grade(grade)

        if not subjects:
            raise EntityNotFound("No se encontraron materias registradas")

        return jsonify([s.to_dict() for s in subjects]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
