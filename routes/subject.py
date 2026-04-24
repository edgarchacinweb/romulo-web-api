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
            SELECT m."MateriaId", m."Nombre", m."FechaCreacion", c."Grado", mh."HorasAcademicas" 
            FROM "MateriaHorasAcademicas" AS mh 
            INNER JOIN "Materia" AS m ON m."MateriaId"=mh."MateriaId" 
            INNER JOIN "Curso" AS c ON c."CursoId"=mh."CursoId"
            WHERE m."Activo"=true
            ORDER BY m."Nombre" ASC, c."Grado" ASC;
        """)
        rows = cursor.fetchall()

        subjects_dict = {}
        for s in rows:
            materia_id = s[0]
            if materia_id not in subjects_dict:
                subjects_dict[materia_id] = {
                    "MateriaId": materia_id,
                    "Nombre": s[1],
                    "Fecha": s[2].strftime("%m/%d/%Y") if s[2] else "",
                    "HorasPorCurso": []
                }
            subjects_dict[materia_id]["HorasPorCurso"].append({
                "Grado": s[3],
                "HorasAcademicas": s[4]
            })

        return jsonify(list(subjects_dict.values())), 200
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

        query = """
            SELECT DISTINCT m."MateriaId", m."Nombre", c."Grado"
            FROM "Materia" m
            INNER JOIN "DocenteMateria" dm ON m."MateriaId" = dm."MateriaId"
            INNER JOIN "MateriaHorasAcademicas" AS mha ON mha."MateriaId"=m."MateriaId"
            INNER JOIN "Curso" AS c ON c."CursoId"=mha."CursoId"
            INNER JOIN "Docente" d ON dm."DocenteId" = d."DocenteId"
            INNER JOIN "Usuario" u ON d."DatosPersonaId" = u."DatosPersona"
            WHERE m."Activo" = true AND u."UsuarioId" = %s;
        """
        
        cursor.execute(query, (usuario_id,))
        rows = cursor.fetchall()
        subject_ids = []
        subjects = []
        schoolgrades = []

        for s in rows:
            subject_ids.append(s[0])
            subjects.append(s[1])
            # schoolgrades.append(list(map(lambda x: x[2], filter(lambda x: x[0] == s[0], rows))))

        subject_ids = set(subject_ids)
        subjects = set(subjects)
        for s in subject_ids:
            schoolgrades.append(list(map(lambda x: x[2], filter(lambda x: x[0] == s, rows))))

        # logger.debug(set(subject_ids))
        # logger.debug(set(subjects))
        logger.debug(schoolgrades)

        return jsonify([{
            "MateriaId": sid,
            "Nombre": s,
            "Grados": sg
        } for sid, s, sg in zip(subject_ids, subjects, schoolgrades)]), 200
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

        if not data.get("HorasAcademicas") or type(data["HorasAcademicas"]) != list:
            raise BadRequest("Las horas academicas deben ser un array")
        elif "Nombre" not in data:
            raise MissingField("Debes indicar el nombre de la materia")
        elif len(data["Nombre"]) < 3:
            raise InsertEntityError("El nombre de la materia debe tener al menos 3 caracteres")

        # Obtener todos los cursos academicos
        cursor.execute("""SELECT "CursoId", "Grado" FROM "Curso" ORDER BY "Grado" ASC;""")
        rows = cursor.fetchall()

        sql = """
        INSERT INTO "Materia" ("Nombre") VALUES (%s) RETURNING "MateriaId";
        """

        cursor.execute(sql, (data["Nombre"],))  
        materia_id = cursor.fetchone()[0]
        
        hoursData = []
        insert_queries = []
        horas_por_curso = []
        for i in range(len(data["HorasAcademicas"])):
            if i < len(rows):
                val = data["HorasAcademicas"][i]
                horas = int(val) if val is not None else 0
                if horas > 0:
                    hoursData.extend([rows[i][0], materia_id, horas])
                    insert_queries.append('(%s, %s, %s)')
                    horas_por_curso.append({
                        "Grado": rows[i][1],
                        "HorasAcademicas": horas
                    })
        
        if insert_queries:
            sql_insert = f"""
                INSERT INTO "MateriaHorasAcademicas" ("CursoId", "MateriaId", "HorasAcademicas") 
                VALUES {','.join(insert_queries)};
            """
            cursor.execute(sql_insert, tuple(hoursData))

        conn.commit()

        cursor.execute('SELECT "FechaCreacion" FROM "Materia" WHERE "MateriaId" = %s', (materia_id,))
        fecha_creacion = cursor.fetchone()[0]

        response_data = {
            "MateriaId": materia_id,
            "Nombre": data["Nombre"],
            "Fecha": fecha_creacion.strftime("%m/%d/%Y") if fecha_creacion else "",
            "HorasPorCurso": horas_por_curso
        }

        return jsonify(response_data), 201
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