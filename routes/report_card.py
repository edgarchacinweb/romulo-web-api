from flask import Blueprint, jsonify, request, Response
from database.Boleta import BoletaRep
from models.Boleta import Boleta
from models.Curso import Curso
from models.Estudiante import Estudiante
from models.Usuario import Rol
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.handler import exception_handler
from database.connection import Connection
from datetime import datetime

rep = BoletaRep()
logger = Logger()

blueprint = Blueprint("report-card", __name__)

@blueprint.route("/report-card/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload and not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            Unauthorized()

        data = request.get_json()

        if not data:
            raise MissingEntityData("No se recibieron datos")
        elif not any(key in data for key in ("EstudianteId", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_uuid(data["EstudianteId"]):
            raise InvalidId("El ID del estudiante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        boleta = Boleta({
            "Estudiante": Estudiante({"id": data["EstudianteId"]}),
            "Curso": Curso({"id": data["CursoId"]})
        })
        id = rep.create(boleta)
        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@blueprint.route("/report-card/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID invático: {id}")

        report_card = rep.get(id)

        return jsonify(report_card.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/report-card/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        affected = rep.delete(id)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@blueprint.route("/report-card/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        limit = None
        offset = None

        if "limit" in request.args:
            limit = int(request.args.get("limit"))
        if "offset" in request.args:
            offset = int(request.args.get("offset"))

        data = rep.list(limit, offset)

        return jsonify([report_card.to_dict() for report_card in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@blueprint.route("/report-card/student/<string:student_id>", methods=["GET"])
def get_student_card(student_id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()

        if not Validations.is_uuid(student_id):
            raise InvalidId(f"ID del estudiante inválido: {student_id}")

        # 1. Obtener lapsos del periodo activo
        cursor.execute('''
            SELECT l."LapsoId", l."Numero", l."FechaInicio", l."FechaFin" 
            FROM "Lapso" l
            JOIN "PeriodoEscolar" pe ON l."PeriodoEscolarId" = pe."PeriodoEscolarId"
            WHERE pe."Activo" = TRUE
            ORDER BY l."Numero" ASC LIMIT 3;
        ''')
        lapsos_rows = cursor.fetchall()

        if not lapsos_rows:
            return jsonify({"message": "No hay lapsos configurados actualmente"}), 404

        lapsos = []
        now = datetime.now().date()
        for r in lapsos_rows:
            lapsos.append({
                "id": r[0],
                "numero": r[1],
                "visible": now >= r[3],
                "fecha_fin": r[3]
            })

        # 2. Obtener grado del estudiante
        cursor.execute('''
            SELECT "CursoId", "Seccion", "PeriodoEscolarId" FROM "CursoEstudiante" 
            WHERE "EstudianteId" = %s AND "PeriodoEscolarId" = (SELECT "PeriodoEscolarId" FROM "PeriodoEscolar" WHERE "Activo" = TRUE LIMIT 1);
        ''', (student_id,))
        curso_row = cursor.fetchone()
        if not curso_row:
             return jsonify({"message": "Estudiante no inscrito en el periodo actual"}), 404
        
        curso_id = curso_row[0]
        seccion = curso_row[1]
        periodo_id = curso_row[2]

        # 3. Obtener materias del curso (con DISTINCT para evitar duplicados en la tabla de horas)
        cursor.execute('''
            SELECT DISTINCT m."MateriaId", m."Nombre" 
            FROM "MateriaHorasAcademicas" mha
            JOIN "Materia" m ON mha."MateriaId" = m."MateriaId"
            WHERE mha."CursoId" = %s
            ORDER BY m."Nombre" ASC;
        ''', (curso_id,))
        materias_rows = cursor.fetchall()

        # 4. Obtener notas actuales
        cursor.execute('''
            SELECT "MateriaId", "LapsoId", "Ponderacion" 
            FROM "Nota" 
            WHERE "EstudianteId" = %s;
        ''', (student_id,))
        notas_rows = cursor.fetchall()
        notas_dict = {(r[0], r[1]): r[2] for r in notas_rows}

        # 5. Obtener inasistencias
        inasistencias_result = []
        for l in lapsos:
            cursor.execute('''
                SELECT c."MateriaId", COUNT(a."AsistenciaId") 
                FROM "Asistencia" a
                JOIN "Clase" c ON a."ClaseId" = c."ClaseId"
                WHERE a."EstudianteId" = %s 
                AND a."Activo" = FALSE
                AND a."FechaCreacion"::date BETWEEN %s AND %s
                GROUP BY c."MateriaId";
            ''', (student_id, lapsos_rows[l["numero"]-1][2], lapsos_rows[l["numero"]-1][3]))
            inasistencias_result.extend([(r[0], l["id"], r[1]) for r in cursor.fetchall()])

        inasistencias_dict = {(r[0], r[1]): r[2] for r in inasistencias_result}

        # 6. Construir respuesta final
        reporte = []
        lapso3_cerrado = lapsos[2]["visible"] if len(lapsos) >= 3 else False

        # Agrupar registros por nombre de materia para consolidar duplicados por ID
        materias_agrupadas = {}
        for m_id, m_nombre in materias_rows:
            if m_nombre not in materias_agrupadas:
                materias_agrupadas[m_nombre] = []
            materias_agrupadas[m_nombre].append(m_id)

        for m_nombre, ids in materias_agrupadas.items():
            row_data = {
                "materia": m_nombre,
                "lapsos": []
            }
            
            total_notas = 0
            count_notas = 0
            total_inasistencias_materia = 0

            for l in lapsos:
                # Consolidar datos de todos los IDs vinculados a este nombre de materia
                nota = None
                inasistencia_lapso = 0
                
                for current_id in ids:
                    # Priorizar el primer registro con nota encontrado
                    val_nota = notas_dict.get((current_id, l["id"]))
                    if val_nota is not None:
                        nota = val_nota
                    
                    # Sumar inasistencias de todos los IDs
                    inasistencia_lapso += inasistencias_dict.get((current_id, l["id"]), 0)
                
                total_inasistencias_materia += inasistencia_lapso
                visible_nota = nota if l["visible"] else None
                
                row_data["lapsos"].append({
                    "numero": l["numero"],
                    "nota": visible_nota,
                    "inasistencias": inasistencia_lapso
                })

                if visible_nota is not None:
                    total_notas += visible_nota
                    count_notas += 1

            # Promedio Final: Solo si el 3er lapso está cerrado
            promedio_final = None
            if lapso3_cerrado and count_notas == 3:
                promedio_final = round(total_notas / 3, 2)
            
            row_data["promedio_final"] = promedio_final
            row_data["total_inasistencias"] = total_inasistencias_materia
            reporte.append(row_data)

        # Calculo de Promedio General
        suma_promedios_generales = 0
        count_materias_con_promedio = 0
        for row_data in reporte:
            if row_data["promedio_final"] is not None:
                suma_promedios_generales += row_data["promedio_final"]
                count_materias_con_promedio += 1

        promedio_general = round(suma_promedios_generales / count_materias_con_promedio, 2) if count_materias_con_promedio > 0 else None

        # Calculo de Promedio Seccion y Posicion
        cursor.execute('''
            SELECT
                n."EstudianteId",
                SUM(n."Ponderacion" * 1.0) / COUNT(n."Ponderacion") as "Promedio_Estudiante"
            FROM "Nota" n
            JOIN "CursoEstudiante" ce ON n."EstudianteId" = ce."EstudianteId"
            WHERE ce."CursoId" = %s AND ce."Seccion" = %s AND ce."PeriodoEscolarId" = %s
            GROUP BY n."EstudianteId"
            ORDER BY "Promedio_Estudiante" DESC;
        ''', (curso_id, seccion, periodo_id))
        ranking_rows = cursor.fetchall()

        posicion_curso = "-"
        promedio_seccion = None

        if len(ranking_rows) > 0:
            suma_ranking = 0
            for index, (est_id, prom) in enumerate(ranking_rows):
                suma_ranking += float(prom)
                if str(est_id) == str(student_id):
                    posicion_curso = f"{index + 1}/{len(ranking_rows)}"
            promedio_seccion = round(suma_ranking / len(ranking_rows), 2)

        # Obtener Docente Guia
        cursor.execute("""
            SELECT dp."Nombre", dp."Apellido" FROM "Horario" h
            JOIN "Docente" d ON h."DocenteId" = d."DocenteId"
            JOIN "DatosPersona" dp ON d."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "Materia" m ON h."MateriaId" = m."MateriaId"
            WHERE h."CursoId"=%s AND h."Seccion"=%s AND h."PeriodoEscolarId"=%s
            AND m."Nombre" ILIKE '%%ORIENTACI%%N%%' AND m."Nombre" ILIKE '%%CONVIVENCIA%%'
            LIMIT 1;
        """, (curso_id, seccion, periodo_id))
        docente_guia_row = cursor.fetchone()
        docente_guia = f"{docente_guia_row[0]} {docente_guia_row[1]}" if docente_guia_row else "Por asignar"

        return jsonify({
            "reporte": reporte,
            "habilitar_pdf": lapso3_cerrado,
            "promedio_general": promedio_general,
            "promedio_seccion": promedio_seccion,
            "posicion_curso": posicion_curso,
            "docente_guia": docente_guia
        }), 200

    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
