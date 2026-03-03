from flask import Blueprint, jsonify, request, Response
from database.connection import Connection
from database.Nota import NotaRep
from models.Nota import Nota
from models.Usuario import Rol
from models.Boleta import Boleta
from models.Materia import Materia
from utils.exceptions import *
from utils.validations import Validations
from utils.Security import Security
from utils.logger import Logger
from utils.handler import  exception_handler

rep = NotaRep()
logger = Logger()

blueprint = Blueprint("calification", __name__)

@blueprint.route("/calification/create", methods=["POST"])
def create():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        data = request.get_json()

        for item in data:
            if not item["Ponderacion"]:
                raise MissingEntityData("La ponderación es requerida")
            elif item["Ponderacion"] < 0 or item["Ponderacion"] > 20:
                raise ValidationError("La calificación debe estar en un rango de 1-20")
            elif not item["MateriaId"]:
                raise MissingEntityData("El ID de la materia es requerido")
            elif not Validations.is_uuid(item["MateriaId"]):
                raise ValidationError("El ID de la materia es inválido")
            elif not item["EstudianteId"]:
                raise MissingEntityData("El ID del estudiante es requerido")
            elif not Validations.is_uuid(item["EstudianteId"]):
                raise ValidationError("El ID del estudiante es inválido")
            elif not item["LapsoId"]:
                raise ValidationError("El lapso es requerido")
            elif not Validations.is_uuid(item["LapsoId"]):
                raise ValidationError("El ID del lapso es inválido")

        # Buscar si existe una nota con la misma MateriaId, EstudianteId y LapsoId
        cursor.execute("""SELECT * FROM "Nota" WHERE "MateriaId"=%s AND "EstudianteId"=%s AND "LapsoId"=%s;""", (item["MateriaId"], item["EstudianteId"], item["LapsoId"]))
        row = cursor.fetchone()
        
        # Actualizar Nota con nueva Ponderacion
        if row:
            cursor.execute("""UPDATE "Nota" SET "Ponderacion"=%s WHERE "MateriaId"=%s AND "EstudianteId"=%s AND "LapsoId"=%s;""", (item["Ponderacion"], item["MateriaId"], item["EstudianteId"], item["LapsoId"]))
        # Crear nuevo registro de Nota
        else:
            cursor.execute("""INSERT INTO "Nota" ("Ponderacion", "MateriaId", "EstudianteId", "LapsoId") VALUES (%s, %s, %s, %s);""", (item["Ponderacion"], item["MateriaId"], item["EstudianteId"], item["LapsoId"]))

        conn.commit()

        return Response(status=201);
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@blueprint.route("/calification/list", methods=["GET"])
def list():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        cursor.execute("""SELECT "NotaId", "Ponderacion", "MateriaId", "EstudianteId", "LapsoId" FROM "Nota";""")
        rows = cursor.fetchall()

        if len(rows) == 0:
            return jsonify([]), 200
        
        return jsonify([{
            "NotaId": n[0],
            "Ponderacion": n[1],
            "MateriaId": n[2],
            "EstudianteId": n[3],
            "LapsoId": n[4]
        } for n in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

