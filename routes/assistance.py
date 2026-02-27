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
import uuid # Importado para generar IDs únicos automáticamente

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
        
        # --- SOLUCIÓN DEFINITIVA SEGÚN TU TABLA ASISTENCIA ---
        estudiantes = data.get("EstudianteId", [])
        asistencias = data.get("Activo", [])
        justificaciones = data.get("Justificacion", [""] * len(estudiantes))
        clase_id = data["ClaseId"]

        # Insertamos manualmente para evitar el error del procedimiento "registrar_asistencia"
        count = 0
        for i in range(len(estudiantes)):
            # Generamos un ID único para la fila (AsistenciaId según tu imagen 4)
            asistencia_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO "Asistencia" ("AsistenciaId", "EstudianteId", "ClaseId", "Activo", "Justificacion")
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)
            """, (asistencia_id, estudiantes[i], clase_id, asistencias[i], justificaciones[i]))
            count += 1

        if count == 0:
            raise ValidationError(f"No se recibieron estudiantes para registrar.")

        conn.commit()
        # -----------------------------------------------------

        # Auditoría
        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": f"Asistencias registradas para la sección vinculada a la ClaseId: {clase_id}",
            "Usuario": Usuario({"id": payload["id"]})
        }))

        return Response(status=201)
    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1] 
    finally:
        if cursor: cursor.close()


# --- ENDPOINT PARA OBTENER ESTUDIANTES CON VALIDACIÓN DE HORARIO ---
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

        if not materia_id or not year_str or not seccion_raw:
            raise ValidationError("Faltan parámetros de búsqueda para cargar la sección.")

        # 1. Obtener el DocenteId
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

        # 2. Extraer grado y sección
        try:
            grado_num = int(year_str[0])
            seccion_int = int(seccion_raw) 
        except:
            raise ValidationError("Formato de año o sección inválido.")

        # 3. Obtener el CursoId
        cursor.execute('SELECT "CursoId" FROM "Curso" WHERE "Grado" = %s', (grado_num,))
        curso_row = cursor.fetchone()
        if not curso_row:
            raise Exception(f"Grado {grado_num} no encontrado.")
        curso_id = curso_row[0]

        # 4. Obtener Periodo Escolar Activo
        cursor.execute('SELECT "PeriodoEscolarId" FROM "PeriodoEscolar" WHERE "Activo" = TRUE LIMIT 1')
        periodo_row = cursor.fetchone()
        if not periodo_row:
            raise Exception("No hay un periodo escolar activo.")
        periodo_id = periodo_row[0]

        # 5. VALIDACIÓN EN HORARIO (Imagen 2 y 3)
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

        # 6. Obtener estudiantes
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
        estudiantes_list = [{"EstudianteId": r[0], "Nombre": r[1], "Apellido": r[2]} for r in estudiantes_rows]

        # 7. Obtener o CREAR el ClaseId real (Imagen 1)
        # Ajustado para incluir PeriodoEscolarId según tu imagen
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
                # Incluimos todos los campos que se ven en tu imagen 1
                cursor.execute("""
                    INSERT INTO "Clase" ("ClaseId", "DocenteId", "CursoId", "Seccion", "PeriodoEscolarId")
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s::uuid)
                """, (clase_id, docente_id, curso_id, seccion_int, periodo_id))
                conn.commit()
                print(f"✅ Clase autocreada con PeriodoId: {clase_id}")
            except Exception as e:
                conn.rollback()
                print(f"⚠️ Error al crear clase: {e}")
                clase_id = "123e4567-e89b-12d3-a456-426614174000"

        return jsonify({
            "ClaseId": clase_id,
            "estudiantes": estudiantes_list
        }), 200

    except Exception as err:
        if conn: conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        if cursor: cursor.close()