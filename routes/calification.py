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
        status = LapsoRules.get_open_lapsos_status()
        
        # Verify if there is any lapso open
        if len(status["open_lapso_ids"]) == 0:
            raise Unauthorized("El proceso de carga de calificaciones se encuentra cerrado. Ningún lapso está abierto.")
        
        data = request.get_json()

        for item in data:
            if item.get("Ponderacion") is None or str(item["Ponderacion"]).strip() == "":
                raise MissingEntityData("La ponderación es requerida")
            
            try:
                pond_val = int(item["Ponderacion"])
            except ValueError:
                raise ValidationError("La calificación debe ser un valor entero numérico")
                
            if not (0 <= pond_val <= 20):
                raise ValidationError("La calificación debe estar en un rango de 0-20")
            item["Ponderacion"] = pond_val
            
            if not item["MateriaId"]:
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
            
            # Security rule: LapsoId must be inside open lapsos
            if item["LapsoId"] not in status["open_lapso_ids"]:
                raise Unauthorized("Está intentando cargar o modificar notas en un lapso que actualmente no se encuentra abierto.")

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

@blueprint.route("/calification/grade_status", methods=["POST"])
def grade_status():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        data = request.get_json()
        student_ids = data.get("StudentIds", [])
        curso_id = data.get("CursoId", "")

        if not student_ids or not curso_id:
            return jsonify({}), 200

        # 1. Count how many active subjects exist for this course
        cursor.execute("""
            SELECT COUNT(DISTINCT mha."MateriaId")
            FROM "MateriaHorasAcademicas" mha
            JOIN "Materia" m ON m."MateriaId" = mha."MateriaId"
            WHERE mha."CursoId" = %s AND m."Activo" = TRUE;
        """, (curso_id,))
        subject_count = cursor.fetchone()[0]

        # 2. Get the 3 lapso IDs for the active school term
        cursor.execute("""
            SELECT l."LapsoId"
            FROM "Lapso" l
            JOIN "PeriodoEscolar" pe ON l."PeriodoEscolarId" = pe."PeriodoEscolarId"
            WHERE pe."Activo" = TRUE
            ORDER BY l."Numero" ASC
            LIMIT 3;
        """)
        lapso_rows = cursor.fetchall()
        lapso_count = len(lapso_rows)

        # Expected total grades per student = subjects × lapsos (3)
        expected_total = subject_count * lapso_count

        if expected_total == 0:
            # No subjects or no lapsos configured => no one can be "complete"
            result = {sid: False for sid in student_ids}
            return jsonify(result), 200

        lapso_ids = [r[0] for r in lapso_rows]

        # 3. Count actual grades per student (only for these lapsos)
        # Build IN clause for student IDs
        placeholders_students = ','.join(['%s'] * len(student_ids))
        placeholders_lapsos = ','.join(['%s'] * len(lapso_ids))

        cursor.execute(f"""
            SELECT n."EstudianteId", COUNT(n."NotaId")
            FROM "Nota" n
            JOIN "MateriaHorasAcademicas" mha ON n."MateriaId" = mha."MateriaId" AND mha."CursoId" = %s
            WHERE n."EstudianteId" IN ({placeholders_students})
              AND n."LapsoId" IN ({placeholders_lapsos})
            GROUP BY n."EstudianteId";
        """, (curso_id, *student_ids, *lapso_ids))
        count_rows = cursor.fetchall()

        # Build result dictionary
        grade_counts = {str(r[0]): int(r[1]) for r in count_rows}
        result = {}
        for sid in student_ids:
            actual = grade_counts.get(str(sid), 0)
            result[str(sid)] = actual >= expected_total

        return jsonify(result), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@blueprint.route("/calification/academic_status", methods=["POST"])
def academic_status():
    """
    Calcula el estatus académico de cada estudiante:
    - Promedio final por materia = promedio de las notas de los 3 lapsos del período activo.
    - Materia reprobada si promedio final <= 9.
    - Retorna { EstudianteId: cantidad_materias_reprobadas } para cada estudiante solicitado.
    """
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        data = request.get_json()
        student_ids = data.get("StudentIds", [])
        curso_id = data.get("CursoId", "")

        if not student_ids or not curso_id:
            return jsonify({}), 200

        # 1. Obtener los IDs de los 3 lapsos del período escolar activo
        cursor.execute("""
            SELECT l."LapsoId"
            FROM "Lapso" l
            JOIN "PeriodoEscolar" pe ON l."PeriodoEscolarId" = pe."PeriodoEscolarId"
            WHERE pe."Activo" = TRUE
            ORDER BY l."Numero" ASC
            LIMIT 3;
        """)
        lapso_rows = cursor.fetchall()
        lapso_ids = [r[0] for r in lapso_rows]

        if len(lapso_ids) == 0:
            result = {sid: 0 for sid in student_ids}
            return jsonify(result), 200

        # 2. Obtener las materias activas del curso
        cursor.execute("""
            SELECT DISTINCT mha."MateriaId"
            FROM "MateriaHorasAcademicas" mha
            JOIN "Materia" m ON m."MateriaId" = mha."MateriaId"
            WHERE mha."CursoId" = %s AND m."Activo" = TRUE;
        """, (curso_id,))
        subject_ids = [r[0] for r in cursor.fetchall()]

        if len(subject_ids) == 0:
            result = {sid: 0 for sid in student_ids}
            return jsonify(result), 200

        # 3. Consulta: para cada estudiante y materia, calcular el promedio
        #    solo si tiene los 3 lapsos cargados; luego contar las reprobadas (promedio <= 9)
        placeholders_students = ','.join(['%s'] * len(student_ids))
        placeholders_lapsos = ','.join(['%s'] * len(lapso_ids))
        placeholders_subjects = ','.join(['%s'] * len(subject_ids))

        query = f"""
            SELECT sub."EstudianteId", COUNT(*) AS materias_reprobadas
            FROM (
                SELECT n."EstudianteId", n."MateriaId",
                       AVG(n."Ponderacion") AS promedio_final,
                       COUNT(n."NotaId") AS total_notas
                FROM "Nota" n
                WHERE n."EstudianteId" IN ({placeholders_students})
                  AND n."LapsoId" IN ({placeholders_lapsos})
                  AND n."MateriaId" IN ({placeholders_subjects})
                GROUP BY n."EstudianteId", n."MateriaId"
                HAVING COUNT(n."NotaId") = {len(lapso_ids)}
                   AND AVG(n."Ponderacion") <= 9
            ) sub
            GROUP BY sub."EstudianteId";
        """

        cursor.execute(query, (*student_ids, *lapso_ids, *subject_ids))
        rows = cursor.fetchall()

        # Construir resultado: por defecto 0 reprobadas para quienes no aparecen en la consulta
        result = {sid: 0 for sid in student_ids}
        for r in rows:
            result[str(r[0])] = int(r[1])

        return jsonify(result), 200
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
                COALESCE(C."Grado"::TEXT || '° Año', 'N/A') AS Ano,
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
            LEFT JOIN LATERAL (
                SELECT CE."CursoId"
                FROM "CursoEstudiante" CE
                JOIN "PeriodoEscolar" PE ON CE."PeriodoEscolarId" = PE."PeriodoEscolarId"
                WHERE CE."EstudianteId" = E."EstudianteId"
                ORDER BY PE."FechaInicio" DESC
                LIMIT 1
            ) CE_LATEST ON TRUE
            LEFT JOIN "Curso" C ON C."CursoId" = CE_LATEST."CursoId"
            ORDER BY HN."FechaCambio" DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        result = [{
            "Estudiante": r[0],
            "Ano": r[1],
            "Materia": r[2],
            "NotaAnterior": r[3],
            "NotaNueva": r[4],
            "Justificacion": r[5],
            "FechaCambio": r[6]
        } for r in rows]


        return jsonify(result), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
