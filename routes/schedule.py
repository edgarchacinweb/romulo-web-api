from flask import Blueprint, request, jsonify, Response
from datetime import datetime, date
from utils.logger import Logger
from utils.handler import exception_handler
from utils.exceptions import * 
from utils.validations import Validations
from utils.Security import Security
from utils.helpers import number_to_letter
from database.connection import Connection
from os import getenv

schedule_bp = Blueprint("schedule", __name__)
logger = Logger()

@schedule_bp.route("/schedule/filter", methods=["POST"])
def filter():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        data = request.get_json()
        
        if "CursoId" not in data or not data["CursoId"]:
            raise MissingEntityData("Debe especificar el grado")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El identificador del grado es inválido")
        elif "Seccion" not in data or not data["Seccion"]:
            raise MissingEntityData("Debe especificar la sección")
        elif not Validations.is_section(data["Seccion"]):
            raise InvalidId("Debes indicar una sección válida ")
        elif "PeriodoEscolarId" not in data or not data["PeriodoEscolarId"]:
            raise MissingEntityData("Debe especificar el período escolar")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("El identificador del período escolar es inválido")

        cursor.execute("""
            SELECT * FROM "Horario" AS h
            INNER JOIN "BloqueHorario" AS bh ON bh."BloqueHorarioId"=h."BloqueHorarioId"
            WHERE h."CursoId"=%s AND h."Seccion"=%s AND h."PeriodoEscolarId"=%s
            ORDER BY bh."HoraInicio" ASC;
        
        """, (data["CursoId"], data["Seccion"], data["PeriodoEscolarId"]) );

        rows = cursor.fetchall()

        # Obtener nombre del Periodo Escolar
        cursor.execute("""
            SELECT "FechaInicio", "FechaFin" FROM "PeriodoEscolar" WHERE "PeriodoEscolarId"=%s
        """, (data["PeriodoEscolarId"],))
        periodo_row = cursor.fetchone()
        periodo_nombre = "Desconocido"
        if periodo_row:
            periodo_nombre = f"{periodo_row[0].year} - {periodo_row[1].year}"

        # Obtener Docente Guía (Materia: ORIENTACION Y CONVIVENCIA)
        cursor.execute("""
            SELECT dp."Nombre", dp."Apellido" FROM "Horario" h
            JOIN "Docente" d ON h."DocenteId" = d."DocenteId"
            JOIN "DatosPersona" dp ON d."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "Materia" m ON h."MateriaId" = m."MateriaId"
            WHERE h."CursoId"=%s AND h."Seccion"=%s AND h."PeriodoEscolarId"=%s
            AND m."Nombre" ILIKE '%%ORIENTACION%%' AND m."Nombre" ILIKE '%%CONVIVENCIA%%'
            LIMIT 1;
        """, (data["CursoId"], data["Seccion"], data["PeriodoEscolarId"]))
        docente_guia_row = cursor.fetchone()
        docente_guia = f"{docente_guia_row[0]} {docente_guia_row[1]}" if docente_guia_row else "Por asignar"

        return jsonify({
            "metadata": {
                "PeriodoEscolarNombre": periodo_nombre,
                "DocenteGuia": docente_guia
            },
            "schedule": [{
                "HorarioId": h[0],
                "Dia": h[1],
                "DocenteId": h[2],
                "MateriaId": h[3],
                "BloqueHorarioId": h[4],
                "CursoId": h[5],
                "PeriodoEscolarId": h[6],
                "Seccion": h[7]
            } for h in rows]
        }), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

    finally:
        cursor.close()

@schedule_bp.route("/schedule/list/<string:periodo_escolar_id>", methods=["GET"])
def list_schedule(periodo_escolar_id = ""):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        if not Validations.is_uuid(periodo_escolar_id):
            raise InvalidId("El identificador del período escolar es inválido")

        cursor.execute("""
            SELECT * FROM "Horario" AS h
            INNER JOIN "BloqueHorario" AS bh ON bh."BloqueHorarioId"=h."BloqueHorarioId"
            WHERE h."PeriodoEscolarId"=%s
            ORDER BY bh."HoraInicio" ASC;
        
        """, (periodo_escolar_id,) );

        rows = cursor.fetchall()

        return jsonify([{
            "HorarioId": h[0],
            "Dia": h[1],
            "DocenteId": h[2],
            "MateriaId": h[3],
            "BloqueHorarioId": h[4],
            "CursoId": h[5],
            "PeriodoEscolarId": h[6],
            "Seccion": h[7],
        } for h in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@schedule_bp.route("/schedule/blocks", methods=["GET"])
def blocks():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        cursor.execute("SELECT * FROM \"BloqueHorario\";")
        rows = cursor.fetchall()

        return jsonify([{
    "BloqueHorarioId": bh[0],
    "HoraInicio": bh[1].strftime("%H:%M") if bh[1] else None,
    "HoraFin": bh[2].strftime("%H:%M") if bh[2] else None
} for bh in rows]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@schedule_bp.route("/schedule/create", methods=["POST"])
def create():
    conn = Connection().get_connection()
    cursor = conn.cursor()

    try:
        payload = Security.verify_token(request.headers)
        if payload is None:
            raise Unauthorized()

        data = request.get_json()

        if not isinstance(data, list):
            raise ValidationError("Los datos deben ser una lista")

        # Seleccionando el período escolar actual
        cursor.execute("SELECT \"PeriodoEscolarId\" FROM \"PeriodoEscolar\" WHERE \"Activo\"=true ORDER BY \"FechaInicio\" DESC LIMIT 1;")
        row = cursor.fetchone()
        if row is None:
            raise InvalidId("No se encontró ningún período escolar activo")

        periodo_escolar_id = row[0]

        # Validación: Mínimo 15 estudiantes inscritos
        if len(data) > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM "CursoEstudiante" ce
                JOIN "EstadoEstudiante" ee ON ce."EstudianteId" = ee."EstudianteId"
                WHERE ce."CursoId" = %s AND ce."Seccion" = %s AND ce."PeriodoEscolarId" = %s AND ee."Estado" = 'inscrito'
            """, (data[0]["CursoId"], data[0]["Seccion"], periodo_escolar_id))
            student_count = cursor.fetchone()[0]
            min_students = int(getenv("MIN_STUDENTS") or 15)
            if student_count < min_students:
                raise ValidationError(f"La sección debe tener al menos {min_students} estudiantes inscritos para asignarle un horario. (Actual: {student_count})")

        for item in data:
            if item.get("MateriaId") == "sin_asignar" or item.get("MateriaId") is None:
                cursor.execute("""
                    DELETE FROM "Horario"
                    WHERE "CursoId"=%s AND "Seccion"=%s AND "PeriodoEscolarId"=%s AND "Dia"=%s AND "BloqueHorarioId"=%s;
                """, (item["CursoId"], item["Seccion"], periodo_escolar_id, item["Dia"], item["BloqueHorarioId"]))
                continue

            if not Validations.is_uuid(item["CursoId"]):
                raise InvalidId("El identificador del curso es inválido")
            elif not Validations.is_uuid(item["BloqueHorarioId"]):
                raise InvalidId("El identificador del bloque horario es inválido")
            elif not Validations.is_uuid(item["DocenteId"]):
                raise InvalidId("El identificador del docente es inválido")
            elif not Validations.is_uuid(item["MateriaId"]):
                raise InvalidId("El identificador de la materia es inválido")
            elif not Validations.is_section(item["Seccion"]):
                raise InvalidId("La sección es inválida")
            elif not Validations.is_day(item["Dia"]):
                raise InvalidId("El día es inválido")

            # Validación: Profesor Guía (Orientación y Convivencia) es único por período escolar
            cursor.execute("SELECT \"MateriaId\" FROM \"Materia\" WHERE \"Nombre\" ILIKE '%ORIENTACION%' AND \"Nombre\" ILIKE '%CONVIVENCIA%' LIMIT 1")
            orientacion_row = cursor.fetchone()
            if orientacion_row and item["MateriaId"] == orientacion_row[0]:
                cursor.execute("""
                    SELECT c."Grado", h."Seccion" FROM "Horario" h
                    JOIN "Curso" c ON h."CursoId" = c."CursoId"
                    WHERE h."DocenteId" = %s AND h."MateriaId" = %s 
                    AND h."PeriodoEscolarId" = %s AND (h."CursoId" != %s OR h."Seccion" != %s)
                """, (item["DocenteId"], item["MateriaId"], periodo_escolar_id, item["CursoId"], item["Seccion"]))
                guide_clash = cursor.fetchone()
                if guide_clash:
                    cursor.execute("SELECT \"Nombre\", \"Apellido\" FROM \"DatosPersona\" dp JOIN \"Docente\" d ON d.\"DatosPersonaId\" = dp.\"DatosPersonaId\" WHERE d.\"DocenteId\" = %s", (item["DocenteId"],))
                    teacher_name = cursor.fetchone()
                    raise ValidationError(f"Error: El docente {teacher_name[0]} {teacher_name[1]} ya es Profesor Guía de {guide_clash[0]}° {number_to_letter(int(guide_clash[1]))}. Seleccione otro docente.")

            # Validación Anti-Choques: Verificar si el docente ya tiene clase en el mismo bloque y día
            cursor.execute("""
                SELECT c."Grado", h."Seccion" FROM "Horario" h
                JOIN "Curso" c ON h."CursoId" = c."CursoId"
                WHERE h."DocenteId" = %s AND h."BloqueHorarioId" = %s AND h."Dia" = %s 
                AND h."PeriodoEscolarId" = %s AND (h."CursoId" != %s OR h."Seccion" != %s)
            """, (item["DocenteId"], item["BloqueHorarioId"], item["Dia"], periodo_escolar_id, item["CursoId"], item["Seccion"]))
            clash = cursor.fetchone()
            if clash:
                cursor.execute("SELECT \"Nombre\", \"Apellido\" FROM \"DatosPersona\" dp JOIN \"Docente\" d ON d.\"DatosPersonaId\" = dp.\"DatosPersonaId\" WHERE d.\"DocenteId\" = %s", (item["DocenteId"],))
                teacher_name = cursor.fetchone()
                raise ValidationError(f"El docente {teacher_name[0]} {teacher_name[1]} ya tiene una clase asignada el día {item['Dia']} en el bloque solicitado (ya asignado a {clash[0]}° {number_to_letter(int(clash[1]))}).")

            # Buscar si existe un horario con el mismo curso, seccion, periodo escolar y dia
            cursor.execute("""
                SELECT * FROM "Horario"
                WHERE "CursoId"=%s AND "Seccion"=%s AND "PeriodoEscolarId"=%s AND "Dia"=%s AND "BloqueHorarioId"=%s
            """, (item["CursoId"], item["Seccion"], periodo_escolar_id, item["Dia"], item["BloqueHorarioId"]))
            row = cursor.fetchone()
            logger.info(row)

            # Actualizar horario con nueva materia y docente
            if row:
                cursor.execute("""
                    UPDATE "Horario"
                    SET "MateriaId"=%s, "DocenteId"=%s
                    WHERE "CursoId"=%s AND "Seccion"=%s AND "PeriodoEscolarId"=%s AND "Dia"=%s AND "BloqueHorarioId"=%s;
                """, (item["MateriaId"], item["DocenteId"], item["CursoId"], item["Seccion"], periodo_escolar_id, item["Dia"], item["BloqueHorarioId"]))
            else:
                cursor.execute("""
                    INSERT INTO "Horario" ("CursoId", "Seccion", "PeriodoEscolarId", "Dia", "BloqueHorarioId", "DocenteId", "MateriaId")
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (item["CursoId"], item["Seccion"], periodo_escolar_id, item["Dia"], item["BloqueHorarioId"], item["DocenteId"], item["MateriaId"]))
        
        # Registrando auditoría
        cursor.execute("SELECT \"Grado\" FROM \"Curso\" WHERE \"CursoId\"=%s", (data[0]["CursoId"],))
        row = cursor.fetchone()
        cursor.execute("""
            INSERT INTO "Auditoria" ("UsuarioId", "Accion", "Descripcion") VALUES (%s, %s, %s)
        """, (payload["id"], "Modificación", f"Actualizado horario de {row[0]}° {number_to_letter(int(data[0]['Seccion']))}"))

        # Consultar todo el horario para regresar cambios
        cursor.execute("""
        SELECT * FROM "Horario" AS h
        INNER JOIN "BloqueHorario" AS bh ON bh."BloqueHorarioId"=h."BloqueHorarioId"
        WHERE h."CursoId"=%s AND h."Seccion"=%s AND h."PeriodoEscolarId"=%s
        ORDER BY bh."HoraInicio" ASC;
        
        """, (data[0]["CursoId"], data[0]["Seccion"], periodo_escolar_id))

        rows = cursor.fetchall()
        conn.commit()

        return jsonify([{
            "HorarioId": h[0],
            "Dia": h[1],
            "DocenteId": h[2],
            "MateriaId": h[3],
            "BloqueHorarioId": h[4],
            "CursoId": h[5],
            "PeriodoEscolarId": h[6],
            "Seccion": h[7]
        } for h in rows]), 201
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@schedule_bp.route("/schedule/admin/status", methods=["GET"])
def admin_status():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if payload is None or payload.get("role") != "ADMIN":
            raise Unauthorized()

        # Obtener periodo activo
        cursor.execute("SELECT \"PeriodoEscolarId\" FROM \"PeriodoEscolar\" WHERE \"Activo\"=true ORDER BY \"FechaInicio\" DESC LIMIT 1;")
        periodo = cursor.fetchone()
        if not periodo:
            return jsonify([]), 200
        
        periodo_id = periodo[0]

        # Obtener total de bloques (recesos excluidos)
        cursor.execute("SELECT * FROM \"BloqueHorario\"")
        all_blocks = cursor.fetchall()
        valid_blocks_count = 0
        for b in all_blocks:
            minutes = (datetime.combine(date.today(), b[2]) - datetime.combine(date.today(), b[1])).seconds / 60
            if minutes > 15:
                valid_blocks_count += 1
        
        total_slots = valid_blocks_count * 5 # 5 dias

        # Obtener todas las secciones y sus datos
        cursor.execute("""
            SELECT c."CursoId", c."Grado", ce."Seccion", COUNT(ce."EstudianteId") as Alumnos
            FROM "CursoEstudiante" ce
            JOIN "Curso" c ON ce."CursoId" = c."CursoId"
            JOIN "EstadoEstudiante" ee ON ce."EstudianteId" = ee."EstudianteId"
            WHERE ce."PeriodoEscolarId" = %s AND ee."Estado" = 'inscrito'
            GROUP BY c."CursoId", c."Grado", ce."Seccion"
            ORDER BY c."Grado" ASC, ce."Seccion" ASC
        """, (periodo_id,))
        
        sections = cursor.fetchall()
        results = []

        for s in sections:
            curso_id, grado, seccion, alumnos = s
            
            # Contar bloques asignados en el horario
            cursor.execute("""
                SELECT COUNT(*) FROM "Horario"
                WHERE "CursoId" = %s AND "Seccion" = %s AND "PeriodoEscolarId" = %s
            """, (curso_id, seccion, periodo_id))
            assigned_count = cursor.fetchone()[0]

            status = "Vacio"
            if assigned_count >= total_slots:
                status = "Completo"
            elif assigned_count > 0:
                status = "Incompleto"

            results.append({
                "CursoId": curso_id,
                "Grado": grado,
                "Seccion": seccion,
                "SeccionLetra": number_to_letter(int(seccion)),
                "Alumnos": alumnos,
                "Estatus": status
            })

        return jsonify(results), 200

    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
