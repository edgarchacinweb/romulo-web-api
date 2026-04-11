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
import uuid

rep = NotaRep()
logger = Logger()

blueprint = Blueprint("calification", __name__)

@blueprint.route("/calification/create", methods=["POST"])
def create():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
            
        from utils.lapso_rules import LapsoRules
        status = LapsoRules.is_calification_open()
        if not status["is_open"]:
            raise Unauthorized("El proceso de carga de calificaciones se encuentra cerrado")
        
        data = request.get_json()

        for item in data:
            if not item["Ponderacion"]:
                raise MissingEntityData("La ponderación es requerida")
            elif int(item["Ponderacion"]) < 0 or int(item["Ponderacion"]) > 20:
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

            # Buscar si existe una nota con la misma MateriaId, EstudianteId y LapsoId bloqueándola para la transacción
            cursor.execute("""SELECT "NotaId", "Ponderacion" FROM "Nota" WHERE "MateriaId"=%s AND "EstudianteId"=%s AND "LapsoId"=%s FOR UPDATE;""", (item["MateriaId"], item["EstudianteId"], item["LapsoId"]))
            row = cursor.fetchone()
            
            # Actualizar Nota con nueva Ponderacion si ha sido modificada
            if row:
                nota_id = row[0]
                nota_anterior = float(row[1])
                nota_nueva = float(item["Ponderacion"])

                if nota_nueva != nota_anterior:
                    justificacion = item.get("Justificacion")
                    if not justificacion or str(justificacion).strip() == "":
                        raise ValidationError("La justificación es obligatoria para editar una calificación ya existente.")
                    
                    cursor.execute("""UPDATE "Nota" SET "Ponderacion"=%s WHERE "NotaId"=%s;""", (item["Ponderacion"], nota_id))
                    historial_id = str(uuid.uuid4())
                    cursor.execute("""INSERT INTO "HistorialNota" ("HistorialId", "NotaId", "NotaAnterior", "NotaNueva", "Justificacion", "UsuarioId", "FechaCambio") VALUES (%s, %s, %s, %s, %s, %s, NOW());""", (historial_id, nota_id, nota_anterior, nota_nueva, justificacion, payload["id"]))
            # Crear nuevo registro de Nota
            else:
                cursor.execute("""INSERT INTO "Nota" ("Ponderacion", "MateriaId", "EstudianteId", "LapsoId") VALUES (%s, %s, %s, %s);""", (item["Ponderacion"], item["MateriaId"], item["EstudianteId"], item["LapsoId"]))

        conn.commit()

        return Response(status=201)
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
        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
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

@blueprint.route("/calification/student/<string:student_id>", methods=["GET"])
def get_by_student(student_id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        logger.debug(payload, Rol.ADMIN.name)
        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.PARENT.name:
            raise Unauthorized()
        
        cursor.execute("""
            SELECT n."NotaId", n."Ponderacion", n."MateriaId", n."EstudianteId", n."LapsoId", l."Numero"
            FROM "Nota" n
            JOIN "Lapso" l ON n."LapsoId" = l."LapsoId"
            WHERE n."EstudianteId"=%s;
        """, (student_id,))
        rows = cursor.fetchall()

        if len(rows) == 0:
            return jsonify([]), 200
        
        return jsonify([{
            "NotaId": n[0],
            "Ponderacion": n[1],
            "MateriaId": n[2],
            "EstudianteId": n[3],
            "LapsoId": n[4],
            "LapsoNumero": n[5]
        } for n in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@blueprint.route("/calification/history", methods=["GET"])
def history():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        query = """
            SELECT 
                DP."Nombre" || ' ' || DP."Apellido" AS Estudiante,
                M."Nombre" AS Materia,
                HN."NotaAnterior",
                HN."NotaNueva",
                HN."Justificacion",
                TO_CHAR(HN."FechaCambio", 'YYYY-MM-DD HH24:MI:SS') AS FechaCambio
            FROM "HistorialNota" HN
            JOIN "Nota" N ON HN."NotaId" = N."NotaId"
            JOIN "Estudiante" E ON N."EstudianteId" = E."EstudianteId"
            JOIN "DatosPersona" DP ON E."DatosPersonaId" = DP."DatosPersonaId"
            JOIN "Materia" M ON N."MateriaId" = M."MateriaId"
            ORDER BY HN."FechaCambio" DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        result = [{
            "Estudiante": r[0],
            "Materia": r[1],
            "NotaAnterior": r[2],
            "NotaNueva": r[3],
            "Justificacion": r[4],
            "FechaCambio": r[5]
        } for r in rows]

        return jsonify(result), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
