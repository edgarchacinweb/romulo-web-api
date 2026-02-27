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
            
            # --- ADAPTADO A TU BASE DE DATOS: Usa FechaCreacion ---
            # Insertamos la fecha del calendario directamente como timestamp
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
            WHERE "DocenteId" = %s AND "CursoId" = %s AND "Seccion" = %s AND "PeriodoEscolarId" = %s
            LIMIT 1
        """, (docente_id, curso_id, seccion_int, periodo_id))
        
        clase_row = cursor.fetchone()
        
        if clase_row:
            clase_id = clase_row[0]
        else:
            clase_id = str(uuid.uuid4())
            try:
                cursor.execute("""
                    INSERT INTO "Clase" ("ClaseId", "DocenteId", "CursoId", "Seccion", "PeriodoEscolarId")
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s::uuid)
                """, (clase_id, docente_id, curso_id, seccion_int, periodo_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                clase_id = "123e4567-e89b-12d3-a456-426614174000"

        # --- CORRECCIÓN: Usamos DATE("FechaCreacion") para omitir la hora y que la comparación no falle ---
        cursor.execute("""
            SELECT "EstudianteId", "Activo", "Justificacion"
            FROM "Asistencia"
            WHERE "ClaseId" = %s AND DATE("FechaCreacion") = %s
        """, (clase_id, fecha_str))
        
        asistencias_existentes = cursor.fetchall()
        asistencia_cargada = len(asistencias_existentes) > 0
        
        # Mapeamos los datos para vincularlos rápido a los estudiantes
        asistencia_dict = {row[0]: {"Activo": row[1], "Justificacion": row[2]} for row in asistencias_existentes}

        estudiantes_list = []
        for r in estudiantes_rows:
            est_id = r[0]
            info_asistencia = asistencia_dict.get(est_id)
            
            estudiantes_list.append({
                "EstudianteId": est_id, 
                "Nombre": r[1], 
                "Apellido": r[2],
                # Si hay registro envía True/False, si no, envía None
                "Presente": info_asistencia["Activo"] if info_asistencia else None,
                "Justificacion": info_asistencia["Justificacion"] if info_asistencia else ""
            })

        return jsonify({
            "ClaseId": clase_id,
            "estudiantes": estudiantes_list,
            "AsistenciaCargada": asistencia_cargada # Enviamos la bandera de bloqueo al JS
        }), 200

    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()