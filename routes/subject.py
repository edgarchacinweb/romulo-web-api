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

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name and payload["role"] != Rol.PARENT.name:
            raise Unauthorized()

        cursor.execute("""
            SELECT m."MateriaId", m."Nombre", m."FechaCreacion", mh."CursoId", mh."HorasAcademicas" FROM "MateriaHorasAcademicas" AS mh INNER JOIN "Materia" AS m ON m."MateriaId"=mh."MateriaId" WHERE m."Activo"=true;
        """)
        rows = cursor.fetchall()

        return jsonify([{
            "MateriaId": s[0],
            "Nombre": s[1],
            "Fecha": s[2].strftime("%m/%d/%Y") if s[2] else "",
            "CursoId": s[3],
            "HorasAcademicas": s[4]
        } for s in rows]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

# --- ENDPOINT PARA OBTENER SOLO LAS MATERIAS DEL DOCENTE ---
@subject_bp.route("/subject/teacher", methods=["GET"])
def teacher_subjects():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        usuario_id = payload["id"]

        # CORRECCIÓN: Nombres de columnas ajustados exactamente a como están en tu Base de Datos
        # d."DatosPersonaId" en la tabla Docente
        # u."DatosPersona" en la tabla Usuario
        query = """
            SELECT DISTINCT m."MateriaId", m."Nombre"
            FROM "Materia" m
            INNER JOIN "DocenteMateria" dm ON m."MateriaId" = dm."MateriaId"
            INNER JOIN "Docente" d ON dm."DocenteId" = d."DocenteId"
            INNER JOIN "Usuario" u ON d."DatosPersonaId" = u."DatosPersona"
            WHERE m."Activo" = true AND u."UsuarioId" = %s;
        """
        
        cursor.execute(query, (usuario_id,))
        rows = cursor.fetchall()

        return jsonify([{
            "MateriaId": s[0],
            "Nombre": s[1]
        } for s in rows]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
# ------------------------------------------------------------------

@subject_bp.route("/subject/create", methods=["POST"])
def create_subject():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data["HorasAcademicas"] or type(data["HorasAcademicas"]) != list:
            raise BadRequest("Las horas academicas deben ser un array")
        elif "Nombre" not in data:
            raise MissingField("Debes indicar el nombre de la materia")
        elif len(data["Nombre"]) < 3:
            raise InsertEntityError("El nombre de la materia debe tener al menos 3 caracteres")

        # Obtener todos los cursos academicos
        cursor.execute("""SELECT "CursoId" FROM "Curso" ORDER BY "Grado" ASC;""")
        rows = cursor.fetchall()

        sql = """
        INSERT INTO "Materia" ("Nombre") VALUES (%s) RETURNING "MateriaId";
        """

        cursor.execute(sql, (data["Nombre"],))  
        materia_id = cursor.fetchone()[0]
        
        hoursData = []
        for i in range(0, 5):
            hoursData.append(rows[i][0])
            hoursData.append(materia_id)
            hoursData.append(str(data["HorasAcademicas"][i]))
        
        sql = """
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") VALUES (%s, %s, %s);
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") VALUES (%s, %s, %s);
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") VALUES (%s, %s, %s);
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") VALUES (%s, %s, %s);
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") VALUES (%s, %s, %s);
        """

        cursor.execute(sql, tuple(hoursData))
        conn.commit()

        return jsonify({"MateriaId": materia_id}), 201
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