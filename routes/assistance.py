from flask import Blueprint, jsonify, request, Response
from utils.handler import exception_handler
from utils.helpers import number_to_letter
from utils.Security import Security
from utils.logger import Logger
from models.Usuario import Rol, Usuario
from utils.exceptions import Unauthorized, ValidationError
from database.Asistencia import AsistenciaRep, Asistencia
from database.Auditoria import AuditoriaRep, Auditoria
from database.Clase import ClaseRep
from database.connection import Connection
from utils.validations import Validations
import uuid 

logger = Logger()
rep = AsistenciaRep()

assistance_bp = Blueprint("assistance", __name__)


@assistance_bp.route("/assistance/create", methods=["POST"])
def create():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not Validations.is_uuid(data["ClaseId"]):
            raise ValidationError("El ID de la clase es inválido")
        
        fecha = data.get("Fecha")
        if not fecha:
             raise ValidationError("Debe especificar la fecha de la asistencia.")

        estudiantes = data.get("EstudianteId", [])
        asistencias = data.get("Activo", [])
        justificaciones = data.get("Justificacion", [""] * len(estudiantes))
        clase_id = data["ClaseId"]

        count = 0
        for i in range(len(estudiantes)):
            asistencia_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO "Asistencia" ("AsistenciaId", "EstudianteId", "ClaseId", "Activo", "Justificacion", "FechaCreacion")
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s::timestamp)
            """, (asistencia_id, estudiantes[i], clase_id, asistencias[i], justificaciones[i], fecha))
            count += 1

        if count == 0:
            raise ValidationError(f"No se recibieron estudiantes para registrar.")

        conn.commit()

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": f"Asistencias registradas para la sección vinculada a la ClaseId: {clase_id} en la fecha {fecha}",
            "Usuario": Usuario({"id": payload["id"]})
        }))

        return Response(status=201)
    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1] 
    finally:
        if cursor: cursor.close()


@assistance_bp.route("/assistance/students", methods=["GET"])
def get_class_students():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized("Solo los docentes pueden consultar sus estudiantes.")

        usuario_id = payload["id"]
        materia_id = request.args.get("materiaId")
        year_str = request.args.get("year")   
        seccion_raw = request.args.get("section") 
        fecha_str = request.args.get("fecha") 

        if not materia_id or not year_str or not seccion_raw or not fecha_str:
            raise ValidationError("Faltan parámetros de búsqueda para cargar la sección.")

        cursor.execute("""
            SELECT d."DocenteId" 
            FROM "Docente" d
            JOIN "Usuario" u ON d."DatosPersonaId" = u."DatosPersona"
            WHERE u."UsuarioId" = %s
        """, (usuario_id,))
        
        docente_row = cursor.fetchone()
        if not docente_row:
            cursor.execute('SELECT "DatosPersona" FROM "Usuario" WHERE "UsuarioId" = %s', (usuario_id,))
            docente_row = cursor.fetchone()
            
        docente_id = docente_row[0]

        try:
            grado_num = int(year_str[0])
            seccion_int = int(seccion_raw) 
        except:
            raise ValidationError("Formato de año o sección inválido.")

        cursor.execute('SELECT "CursoId" FROM "Curso" WHERE "Grado" = %s', (grado_num,))
        curso_row = cursor.fetchone()
        if not curso_row:
            raise Exception(f"Grado {grado_num} no encontrado.")
        curso_id = curso_row[0]

        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoEscolar" WHERE "Activo" = TRUE LIMIT 1')
        periodo_row = cursor.fetchone()
        if not periodo_row:
            raise Exception("No hay un periodo escolar activo.")
        periodo_id = periodo_row[0]

        cursor.execute("""
            SELECT 1 FROM "Horario"
            WHERE "DocenteId" = %s 
              AND "MateriaId" = %s 
              AND "CursoId" = %s 
              AND "Seccion" = %s 
              AND "PeriodoEscolarId" = %s
            LIMIT 1
        """, (docente_id, materia_id, curso_id, seccion_int, periodo_id))

        if not cursor.fetchone():
            return jsonify({
                "message": "Acceso denegado. No tienes esta sección asignada en tu horario oficial."
            }), 403

        cursor.execute("""
            SELECT e."EstudianteId", dp."Nombre", dp."Apellido"
            FROM "Estudiante" e
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "CursoEstudiante" ce ON e."EstudianteId" = ce."EstudianteId"
            JOIN "EstadoEstudiante" ee ON e."EstudianteId" = ee."EstudianteId"
            WHERE ce."CursoId" = %s AND ce."Seccion" = %s AND ce."PeriodoEscolarId" = %s AND ee."Estado" = 'inscrito'
            ORDER BY dp."Apellido" ASC, dp."Nombre" ASC
        """, (curso_id, seccion_int, periodo_id))

        estudiantes_rows = cursor.fetchall()

        cursor.execute("""
            SELECT "ClaseId" FROM "Clase" 
            WHERE "DocenteId" = %s AND "CursoId" = %s AND "Seccion" = %s AND "PeriodoEscolarId" = %s AND "MateriaId" = %s
            LIMIT 1
        """, (docente_id, curso_id, seccion_int, periodo_id, materia_id))
        
        clase_row = cursor.fetchone()
        
        if clase_row:
            clase_id = clase_row[0]
        else:
            clase_id = str(uuid.uuid4())
            try:
                cursor.execute("""
                    INSERT INTO "Clase" ("ClaseId", "DocenteId", "CursoId", "Seccion", "PeriodoEscolarId", "MateriaId")
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s::uuid, %s::uuid)
                """, (clase_id, docente_id, curso_id, seccion_int, periodo_id, materia_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                clase_id = "123e4567-e89b-12d3-a456-426614174000"

        cursor.execute("""
            SELECT "EstudianteId", "Activo", "Justificacion"
            FROM "Asistencia"
            WHERE "ClaseId" = %s AND DATE("FechaCreacion") = %s
        """, (clase_id, fecha_str))
        
        asistencias_existentes = cursor.fetchall()
        asistencia_cargada = len(asistencias_existentes) > 0
        
        asistencia_dict = {row[0]: {"Activo": row[1], "Justificacion": row[2]} for row in asistencias_existentes}

        estudiantes_list = []
        for r in estudiantes_rows:
            est_id = r[0]
            info_asistencia = asistencia_dict.get(est_id)
            
            estudiantes_list.append({
                "EstudianteId": est_id, 
                "Nombre": r[1], 
                "Apellido": r[2],
                "Presente": info_asistencia["Activo"] if info_asistencia else None,
                "Justificacion": info_asistencia["Justificacion"] if info_asistencia else ""
            })

        return jsonify({
            "ClaseId": clase_id,
            "estudiantes": estudiantes_list,
            "AsistenciaCargada": asistencia_cargada
        }), 200

    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()

# --- REPORTE DIARIO PARA ADMINISTRADOR ---
@assistance_bp.route("/assistance/admin/report", methods=["GET"])
def get_admin_report():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("Solo los administradores pueden consultar este reporte.")

        curso_id = request.args.get("cursoId")
        seccion_raw = request.args.get("seccion")
        fecha_str = request.args.get("fecha")
        docente_id = request.args.get("docenteId") # Opcional
        materia_id = request.args.get("materiaId") # Opcional

        if not curso_id or not seccion_raw or not fecha_str:
            raise ValidationError("Faltan parámetros de búsqueda (curso, sección o fecha).")
            
        try:
            seccion_int = int(seccion_raw)
        except:
            raise ValidationError("Formato de sección inválido.")

        # Realizamos el JOIN real a las tablas Asistencia, Estudiante, DatosPersona y Clase
        query = """
            SELECT a."AsistenciaId", a."Activo", a."Justificacion", 
                   dp."Nombre", dp."Apellido"
            FROM "Asistencia" a
            JOIN "Estudiante" e ON a."EstudianteId" = e."EstudianteId"
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "Clase" c ON a."ClaseId" = c."ClaseId"
            WHERE c."CursoId" = %s AND c."Seccion" = %s AND DATE(a."FechaCreacion") = %s
        """
        params = [curso_id, seccion_int, fecha_str]

        # Si filtró por docente, añadimos la condición a la tabla Clase
        if docente_id and docente_id != "undefined" and docente_id != "":
            query += ' AND c."DocenteId" = %s'
            params.append(docente_id)

        # Si filtró por materia, añadimos la condición a la tabla Clase para reportes
        if materia_id and materia_id != "undefined" and materia_id != "":
            query += ' AND c."MateriaId" = %s'
            params.append(materia_id)

        query += ' ORDER BY dp."Apellido" ASC, dp."Nombre" ASC'

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        asistencias_list = []
        for r in rows:
            asistencias_list.append({
                "AsistenciaId": r[0],
                "Activo": r[1],
                "JustificacionDocente": r[2] if r[2] else "",
                "NombreEstudiante": f"{r[3]} {r[4]}".strip(),
                "EditadoPorAdmin": False, # Retornamos False por defecto para no romper el FrontEnd
                "NotaAdmin": "" 
            })

        return jsonify({"asistencias": asistencias_list}), 200
        
    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()

# --- NUEVA RUTA: REPORTE CONSOLIDADO POR LAPSOS (ACTUALIZADA CON CÉDULA) ---
@assistance_bp.route("/assistance/admin/report_lapso", methods=["GET"])
def get_admin_report_lapso():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("Solo los administradores pueden consultar este reporte.")

        curso_id = request.args.get("cursoId")
        seccion_raw = request.args.get("seccion")
        materia_id = request.args.get("materiaId") # Opcional, para ver 1 sola materia
        anio_escolar = request.args.get("anioEscolar", "2025-2026") # Año por defecto

        if not curso_id or not seccion_raw:
            raise ValidationError("Faltan parámetros de búsqueda (curso o sección).")

        seccion_int = int(seccion_raw)

        # Usamos la consulta maestra agrupada, AHORA INCLUYENDO dp."Cedula"
        query = """
            SELECT 
                e."EstudianteId",
                dp."Nombre",
                dp."Apellido",
                dp."Cedula", 
                m."Nombre" AS "NombreMateria",
                l."Numero" AS "LapsoNumero",
                SUM(CASE WHEN a."Activo" = true THEN 1 ELSE 0 END) AS "TotalAsistencias",
                SUM(CASE WHEN a."Activo" = false THEN 1 ELSE 0 END) AS "TotalInasistencias"
            FROM "Asistencia" a
            JOIN "Estudiante" e ON a."EstudianteId" = e."EstudianteId"
            JOIN "DatosPersona" dp ON e."DatosPersonaId" = dp."DatosPersonaId"
            JOIN "Clase" c ON a."ClaseId" = c."ClaseId"
            JOIN "Materia" m ON c."MateriaId" = m."MateriaId"
            JOIN "Lapso" l ON a."FechaCreacion"::date BETWEEN l."FechaInicio" AND l."FechaFin"
            WHERE c."CursoId" = %s AND c."Seccion" = %s AND l."AñoEscolar" = %s
        """
        params = [curso_id, seccion_int, anio_escolar]

        if materia_id and materia_id != "undefined" and materia_id != "":
            query += ' AND c."MateriaId" = %s'
            params.append(materia_id)

        # Añadimos dp."Cedula" al GROUP BY
        query += ' GROUP BY e."EstudianteId", dp."Nombre", dp."Apellido", dp."Cedula", m."Nombre", l."Numero" ORDER BY dp."Apellido" ASC, dp."Nombre" ASC, m."Nombre" ASC, l."Numero" ASC'

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Estructuramos la data en un JSON limpio para el Frontend
        estudiantes_map = {}
        for r in rows:
            est_id = r[0]
            nombre_completo = f"{r[2]} {r[1]}".strip()
            cedula = r[3]
            materia = r[4]
            lapso = int(r[5])
            asistencias = int(r[6])
            inasistencias = int(r[7])

            if est_id not in estudiantes_map:
                estudiantes_map[est_id] = {
                    "EstudianteId": est_id,
                    "NombreEstudiante": nombre_completo,
                    "Cedula": cedula, # AGREGADA AL JSON
                    "Materias": {}
                }

            if materia not in estudiantes_map[est_id]["Materias"]:
                estudiantes_map[est_id]["Materias"][materia] = {
                    "1": {"A": 0, "I": 0},
                    "2": {"A": 0, "I": 0},
                    "3": {"A": 0, "I": 0}
                }

            if lapso in [1, 2, 3]:
                estudiantes_map[est_id]["Materias"][materia][str(lapso)]["A"] = asistencias
                estudiantes_map[est_id]["Materias"][materia][str(lapso)]["I"] = inasistencias

        # Convertimos a Lista
        reporte = list(estudiantes_map.values())

        return jsonify({"reporte_lapsos": reporte}), 200

    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()

# --- EDICIÓN POR ADMINISTRADOR ---
@assistance_bp.route("/assistance/admin/edit/<string:asistencia_id>", methods=["PUT"])
def edit_admin_report(asistencia_id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("Solo los administradores pueden editar asistencias.")

        data = request.get_json()
        nuevo_activo = data.get("Activo")
        
        # Solo actualizamos el estado "Activo"
        cursor.execute("""
            UPDATE "Asistencia" 
            SET "Activo" = %s
            WHERE "AsistenciaId" = %s
        """, (nuevo_activo, asistencia_id))

        conn.commit()

        # Auditoria de quien realizó el cambio
        AuditoriaRep().create(Auditoria({
            "Accion": "Edición",
            "Descripcion": f"Asistencia editada por Administrador para AsistenciaId: {asistencia_id}",
            "Usuario": Usuario({"id": payload["id"]})
        }))

        return jsonify({"message": "Asistencia actualizada."}), 200
    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()