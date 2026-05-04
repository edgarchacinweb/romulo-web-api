from flask import Blueprint, jsonify, request, Response, send_file
from utils.handler import exception_handler
from utils.Security import Security
from utils.logger import Logger
from models.Usuario import Rol
from utils.exceptions import Unauthorized, BackupException
from datetime import datetime
from os import listdir, path, getcwd, makedirs, remove
from datetime import datetime
import database.connection

logger = Logger()
conn = database.connection.Connection()

backup_bp = Blueprint("backup", __name__)

@backup_bp.route("/backup/database", methods=["POST"])
def db_backup():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        backup_dir = path.join(getcwd(), "backups")

        if not path.isdir(backup_dir):
            makedirs(backup_dir)

        backup_file = conn.backup_db()
        logger.debug(backup_file, "BACKUP_FILE")
        logger.debug(listdir(backup_dir), "BACKUP_DIR")

        # 1. Unimos la carpeta backups con el nombre del archivo
        full_path = path.join(backup_dir, backup_file)

        # 2. Revisamos si existe usando la ruta completa
        if not path.exists(full_path):
            logger.error(f"No se creó el archivo de respaldo de la base de datos: {full_path}")
            raise BackupException("No se pudo crear el respaldo de la base de datos")

        return jsonify({"Archivo": backup_file}), 200
    except Exception as err:
        logger.error(str(err))
        return jsonify({"error": True, "message": "Hubo un error al intentar generar el respaldo de la BBDD", "details": str(err)}), 500
    
@backup_bp.route("/backup/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = [{
            "Fecha": i.split("_")[0],
            "Hora": datetime.strptime(":".join(i.split("_")[1:3]), "%H:%M").strftime("%I:%M %p"),
            "Peso": path.getsize(f"backups/{i}"),
            "Archivo": i
        } for i in listdir("backups")]

        data.sort(
            key=lambda x: datetime.strptime(f"{x['Fecha']} {x['Hora']}", "%d-%m-%Y %I:%M %p"),
            reverse=True
        )

        return jsonify(data), 200
    except Exception as err:
        return jsonify([]), 404

@backup_bp.route("/backup/download/<string:file>", methods=["GET"])
def download(file):
    try:
        # payload = Security.verify_token(request.headers)

        # if not payload or payload["role"] != Rol.ADMIN.name:
            # raise Unauthorized()

        file_path = path.join(getcwd(), "backups", file)
        if not path.exists(file_path):
            raise Exception("No se encontró el archivo de respaldo específicado")

        return send_file(file_path, as_attachment=True, download_name=file)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@backup_bp.route("/backup/delete/<string:file>", methods=["DELETE"])
def delete(file):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        file = path.join(getcwd(), "backups", file)
        
        if not path.exists(file):
            raise Exception("No se encontró el archivo de respaldo específicado")

        remove(file)
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
