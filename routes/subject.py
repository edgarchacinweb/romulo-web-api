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

@subject_bp.route("/subject/list", methods=["GET"])
def list_subjects():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        cursor.execute("SELECT * FROM \"Materia\" WHERE \"Activo\" = true;")
        rows = cursor.fetchall()

        return jsonify([{
            "MateriaId": s[0],
            "Nivel": s[1],
            "Nombre": s[2]
        } for s in rows]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@subject_bp.route("/subject/create", methods=["POST"])
def create_subject():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if "Nivel" not in data:
            raise MissingField("Debes indicar si la materia pertenece a un nivel de secundaria o de bachillerato")
        elif data["nivel"] not in ["Secundaria", "Bachillerato"]:
            raise BadRequest("El nivel debe ser 'Secundaria' o 'Bachillerato'")
        elif "Nombre" not in data:
            raise MissingField("Debes indicar el nombre de la materia")
        elif len(data["Nombre"]) < 3:
            raise InsertEntityError("El nombre de la materia debe tener al menos 3 caracteres")
        elif not Validations.is_subject(data["Nombre"]):
            raise InsertEntityError("El nombre de la materia tiene un formato inválido")

        cursor.execute("INSERT INTO \"Materia\" (\"Nivel\", \"Nombre\") VALUES (%s, %s); RETURNING \"MateriaId\"", (data["nivel"], data["nombre"]))
        conn.commit()
        subject_id = cursor.fetchone()[0]

        return jsonify({"MateriaId": subject_id}), 201
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@subject_bp.route("/subject/delete/<string:id>", methods=["DELETE"])
def delete_subject(id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise BadRequest("El ID de la materia es inválido")

        cursor.execute("UPDATE \"Materia\" SET \"Activo\" = false WHERE \"MateriaId\" = %s;", (id,))
        conn.commit()

        return Response(status=200)
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
