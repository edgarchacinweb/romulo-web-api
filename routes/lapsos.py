from flask import Blueprint, jsonify, request, Response
from models.Usuario import Rol, Usuario
from models.Auditoria import Auditoria
from utils.exceptions import *
from utils.Security import Security
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from database.connection import Connection

# Definimos el blueprint para las rutas de los lapsos
lapsos_bp = Blueprint("lapsos", __name__)

@lapsos_bp.route("/lapsos/current", methods=["GET"])
def get_current_lapsos():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        # Verificar la identidad del usuario (Docentes y Admins pueden consultar)
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]:
            raise Unauthorized()

        # Buscar los lapsos del año escolar actual (ordenados del 1 al 3)
        cursor.execute('SELECT "LapsoId","Numero", "FechaInicio", "FechaFin", "AñoEscolar" FROM "Lapso" ORDER BY "Numero" ASC LIMIT 3;')
        rows = cursor.fetchall()

        if not rows:
            # Si no hay datos, retornamos un 404 para que el Front-end ponga las fechas por defecto
            return jsonify({"message": "No hay lapsos configurados actualmente"}), 404

        # Estructurar los datos tal como los espera la interfaz web
        lapsos_data = []
        for row in rows:
            lapsos_data.append({
                "lapso_id": row[0],
                "lapso": row[1],
                "fecha_incio": row[2].strftime("%Y-%m-%d"),
                "fecha_fin": row[3].strftime("%Y-%m-%d")
            })

        return jsonify({
            "año_escolar": rows[0][4],
            "lapsos": lapsos_data
        }), 200

    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()


@lapsos_bp.route("/lapsos/create", methods=["POST"])
def create_lapsos():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        # Solo los administradores pueden guardar/modificar las fechas
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized("No tienes permisos para configurar el calendario escolar")

        data = request.get_json()

        if "lapsos" not in data or "año_escolar" not in data:
            raise BadRequest("Faltan los datos de los lapsos o el año escolar")

        # 1. Eliminamos la configuración anterior de este año escolar para evitar duplicados
        cursor.execute('DELETE FROM "Lapso" WHERE "AñoEscolar" = %s;', (data["año_escolar"],))

        # 2. Insertamos las 3 nuevas fechas
        for lapso in data["lapsos"]:
            cursor.execute(
                'INSERT INTO "Lapso" ("Numero", "FechaInicio", "FechaFin", "AñoEscolar") VALUES (%s, %s, %s, %s);',
                (lapso["lapso"], lapso["fecha_inicio"], lapso["fecha_fin"], data["año_escolar"])
            )
        
        conn.commit()

        # 3. Guardamos la acción en el historial de Auditoría (opcional pero recomendado)
        AuditoriaRep().create(Auditoria({
            "Accion": "Configuración",
            "Descripcion": f"El administrador configuró las fechas de los lapsos para el periodo {data['año_escolar']}",
            "Usuario": Usuario({"id": payload["id"]})
        }))

        return jsonify({"message": "Lapsos configurados exitosamente"}), 201

    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@lapsos_bp.route("/lapsos/get", methods=["GET"])
def get_lapsos():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]:
            raise Unauthorized()
    
        cursor.execute('SELECT "LapsoId", "Numero", "FechaInicio", "FechaFin", "AñoEscolar" FROM "Lapso" WHERE CURRENT_DATE BETWEEN "FechaInicio" AND "FechaFin";')
        rows = cursor.fetchall()

        if len(rows) == 0:
            return Response(status=404)

        row = rows[0]
        return jsonify({
            "LapsoId": row[0],
            "Numero": row[1],
            "FechaInicio": row[2].strftime("%Y-%m-%d"),
            "FechaFin": row[3].strftime("%Y-%m-%d"),
            "AñoEscolar": row[4]
        }), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@lapsos_bp.route("/lapsos/list", methods=["GET"])
def list():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] not in [Rol.ADMIN.name, Rol.TEACHER.name]:
            raise Unauthorized()
    
        cursor.execute('SELECT "LapsoId", "Numero", "FechaInicio", "FechaFin", "AñoEscolar" FROM "Lapso" ORDER BY "FechaInicio" DESC')
        rows = cursor.fetchall()

        if len(rows) == 0:
            return Response(status=404)

        return jsonify([{
            "LapsoId": row[0],
            "Numero": row[1],
            "FechaInicio": row[2].strftime("%Y-%m-%d"),
            "FechaFin": row[3].strftime("%Y-%m-%d"),
            "AñoEscolar": row[4]
        } for row in rows]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()