from flask import Blueprint, jsonify, request, Response
from database.connection import Connection
from database.Usuario import UsuarioRep
from utils.exceptions import *
from models.Usuario import Usuario, Rol
from models.Auditoria import Auditoria
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.config import bcrypt
from utils.handler import exception_handler
from utils.email import send_email
from database.Auditoria import AuditoriaRep
from database.DatosPersona import DatosPersonaRep
from utils.config import app
from utils.image import convert_to_webp, resize, get_format
from pathlib import Path
from PIL import Image
import os

rep = UsuarioRep()
peopleRep = DatosPersonaRep()
logger = Logger()
auditory = AuditoriaRep()

user_bp = Blueprint("users", __name__)

@user_bp.route("/user/encrypt_pwd/<string:pwd>", methods=["GET"])
def encryptpwd(pwd: str):
    try:
        if len(pwd) == 0:
            raise MissingEntityData("Debes envíar una contraseña como parámetro.")

        if "V!" in pwd:
            pwd = pwd.replace("V!", "V#")
        
        password = bcrypt.generate_password_hash(pwd, rounds=int(os.getenv("pwd_rounds"))).decode("utf-8")

        return jsonify({"password": password})
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if not data:
            raise MissingEntityData("No se recibieron datos")
        elif not any(key in data for key in ("Email", "Rol", "DatosPersonaId")):
            raise MissingEntityData("Faltan datos para realizar la operación")
        
        user_response = rep.get_by_people_id(data["DatosPersonaId"])
        logger.debug("Datos del usuario buscados")

        if user_response and len(user_response) > 0:
            return jsonify({"id": user_response[0]}), 200

        if not Validations.is_email(data["Email"]):
            raise ValidationError("El correo electrónico introducido no es valido")
        
        # --- VALIDACIÓN NUEVA DE DOMINIO DE CORREO ---
        email_domain = data["Email"].split('@')[1].lower()
        allowed_domains = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"]
        if email_domain not in allowed_domains:
            raise ValidationError("Solo se permiten correos: Gmail, Outlook, Hotmail o Yahoo")
        # ---------------------------------------------

        elif not any(r in data["Rol"] for r in (Rol.PARENT.value, Rol.TEACHER.value)):
            raise ValidationError("Sólo puedes registrar un representante o un docente")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido")
        
        logger.debug("Validaciones realizadas")

        # --- CORRECCIÓN DE ENCRIPTACIÓN DE CONTRASEÑA ---
        if not "Clave" in data or not data["Clave"]:
            raw_password = Security.generate_password()
            logger.debug("Clave generada")
        else:
            raw_password = data["Clave"]

        # AQUÍ ENCRIPTAMOS LA CONTRASEÑA CON SALT ANTES DE GUARDARLA
        hashed_password = bcrypt.generate_password_hash(raw_password, rounds=int(os.getenv("pwd_rounds"))).decode("utf8")

        user: Usuario = Usuario({
            "Email": data["Email"],
            "Clave": hashed_password, # Usamos la contraseña ya encriptada (hash)
            "Rol": Rol.PARENT if data["Rol"] == Rol.PARENT.value else Rol.TEACHER,
            "DatosPersonaId": data["DatosPersonaId"]
        })
        # ------------------------------------------------

        id = rep.create(user)

        logger.debug("Usuario creado")

        if not id:
            raise InsertEntityError("No se pudo crear el usuario")


        auditory.create(Auditoria({
            "Accion": "Registro",
            "Descripcion": f"Usuario {data['Rol']} creado",
            "Usuario": Usuario({
                "id": id
            })
        }))

        logger.debug("Auditoria creada")

        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/login", methods=["POST"])
def login():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        data = request.get_json()

        if not "Email" in data or not "Clave" in data:
            raise MissingEntityData("Falta correo electrónico o contraseña.")
        
        cursor.execute("SELECT \"UsuarioId\", \"Clave\" FROM \"Usuario\" WHERE \"Email\" = %s;", (data["Email"],))
        auth = cursor.fetchone()
        if not auth:
            raise EntityNotFound("No se encontró a ningún usuario con ese correo electrónico")
        
        logger.debug(bcrypt.check_password_hash(auth[1], data["Clave"]))
        if not bcrypt.check_password_hash(auth[1], data["Clave"]):
            raise ValidationError("Contraseña inválida")
        
        auditory.create(Auditoria({
            "Accion": "Sesión",
            "Descripcion": "Inicio de sesión realizado",
            "Usuario": Usuario({
                "id": auth[0]
            })
        }))

        return jsonify({"id": auth[0]}), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@user_bp.route("/user/get", methods=["GET"])
def get_user():
    try:
        payload = Security.verify_token(request.headers)
        
        if not payload:
            raise Unauthorized()

        if not Validations.is_uuid(payload["id"]):
            raise InvalidId(F"ID inválido: {payload['id']}")
        
        user = rep.get(payload["id"])
        return jsonify(user.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]    

@user_bp.route("/user/get", methods=["GET"])
@user_bp.route("/user/get/<string:ci>", methods=["GET"])
def get(ci: str):
    try:
        payload = Security.verify_token(request.headers)
        
        if not payload:
            raise Unauthorized()

        if not Validations.is_uuid(payload["id"]):
            raise InvalidId(F"ID inválido: {payload['id']}")
        
        user = None
        if not ci:
            user = rep.get(payload["id"])
        else:
            people = peopleRep.get_by_ci(ci)
            userResult = rep.get_by_people_id(people.id)
            user = rep.get(userResult)
            user.password = None
            logger.debug(user.to_dict())
        logger.debug(user.to_dict(), "/user/get")
        user_dict = user.to_dict()
        del user_dict["Clave"]
        return jsonify(user_dict), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@user_bp.route("/user/token/<string:id>", methods=["GET"])
def token(id: str):
    try:
        if not Validations.is_uuid(id):
            raise InvalidId(F"ID inválido: {id}")

        user = rep.get(id)

        if not user:
            raise EntityNotFound("No se encontró el usuario")

        token = Security.generateToken(user)
        return jsonify({"token": token, "role": user.role.value}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/list", methods=["GET"])
def list_users():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        users = rep.list()
        
        if not users:
            raise EntityNotFound("No se encontraron usuarios registrados")

        for i in users:
            logger.info(i)

        return jsonify([u.to_dict() for u in users]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/get/rol/<int:ci>", methods=["GET"])
def get_rol(ci: int):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_ci(str(ci)):
            raise ValidationError(F"Cédula de identidad inválida")

        user = rep.get_role_by_ci(ci)

        return jsonify({"role": user.role.value}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/filter", methods=["POST"])
def filter():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data:
            data = { "Rol": Rol.TEACHER.value }
        elif "Rol" not in data:
            data["Rol"] = Rol.TEACHER.value 
        
        if "Email" in data and len(data["Email"]) > 0 and not Validations.is_email(data["Email"]):
            raise ValidationError("El correo no es válido")
        if "Rol" in data and not any(r in data["Rol"] for r in (Rol.PARENT.value, Rol.TEACHER.value)):
            raise ValidationError("Sólo puedes filtrar por representantes o docentes")
        
        offset = request.args.get("offset")
        limit = request.args.get("limit")
        if offset != None:        
            offset = int(offset)
        if limit != None:
            limit = int(limit)

        filters = { "Rol": data["Rol"] }
        if "Nombre" in data and len(data["Nombre"]) > 0:
            filters["Nombre"] = data["Nombre"]
        if "Apellido" in data and len(data["Apellido"]) > 0:
            filters["Apellido"] = data["Apellido"]
        if "Cedula" in data and len(data["Cedula"]) > 0:
            filters["Cedula"] = data["Cedula"]
        if "Email" in data and len(data["Email"]) > 0:
            filters["Email"] = data["Email"]

        users = rep.filter(limit=limit, offset=offset, filters=filters)
        return jsonify([u.to_dict() for u in users]), 200

    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/modify/password", methods=["PATCH"])
def modify_password():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        data = request.get_json()

        if not data or "Password" not in data:
            raise ValidationError("Debes enviar la nueva contraseña")
        elif "RPassword" not in data:
            raise ValidationError("Debes enviar la contraseña de confirmación")
        elif "Email" not in data:
            raise ValidationError("Debes enviar el correo electrónico")
        elif not Validations.is_email(data["Email"]):
            raise ValidationError("El correo electrónico no es válido")
        
        password, rpassword = data["Password"], data["RPassword"]

        if (password != rpassword):
            raise ValidationError("Las contraseñas no coinciden")
        
        new_password = bcrypt.generate_password_hash(password, int(os.getenv("pwd_rounds"))).decode("utf8")
        cursor.execute("UPDATE \"Usuario\" SET \"Clave\"=%s WHERE \"Email\"=%s", (new_password, data["Email"]))
        conn.commit()

        logger.info(f"Contraseña modificada para el usuario con correo {data['Email']}")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

# --- FUNCIÓN DEFINITIVA Y ROBUSTA ---
@user_bp.route("/user/parent/update", methods=["PATCH"])
def update_parent():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    have_dni = False
    have_carnet = False
    payload = None # Evita el error 500 en el except

    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.PARENT.name:
            raise Unauthorized()
        elif not Validations.is_uuid(payload['id']):
            raise InvalidId(f"ID inválido: {payload['id']}")

        data = request.form
        files = request.files

        data_to_update = {}

        # 1. Recuperación inteligente de datos (Busca "Telefono" O "telefono")
        phone = data.get("Telefono") or data.get("telefono")
        ocupacion = data.get("Ocupacion") or data.get("ocupacion")
        direccion = data.get("Direccion") or data.get("direccion")
        clave = data.get("Clave") or data.get("clave")

        # 2. Validaciones y asignación
        if phone and len(phone) > 0:
            if not Validations.is_phone(phone):
                raise ValidationError("El teléfono no es válido")
            data_to_update["Telefono"] = phone

        if ocupacion and len(ocupacion) > 0:
            data_to_update["Ocupacion"] = ocupacion

        if direccion and len(direccion) > 0:
            data_to_update["Direccion"] = direccion

        # 3. Lógica de Contraseña
        if clave and len(clave) > 0:
            if not Validations.is_password(clave):
                raise ValidationError("La contraseña nueva no cumple con el formato requerido")
            
            rclave = data.get("RClave") or data.get("rclave")
            if not rclave:
                raise ValidationError("Debes confirmar la nueva contraseña")
            elif clave != rclave:
                raise ValidationError("Las contraseñas nuevas no coinciden")

            cursor.execute("SELECT \"Clave\" FROM \"Usuario\" WHERE \"UsuarioId\" = %s", (payload["id"],))
            result = cursor.fetchone()
            
            if not result:
                raise EntityNotFound("No se encontró el usuario")
            
            vclave = data.get("VClave") or data.get("vclave")
            if not vclave:
                 raise ValidationError("Debes ingresar tu contraseña actual para realizar el cambio")

            if not bcrypt.check_password_hash(result[0], vclave):
                raise ValidationError("La contraseña actual es incorrecta")

            new_password = bcrypt.generate_password_hash(clave, int(os.getenv("pwd_rounds"))).decode("utf8")
            cursor.execute("UPDATE \"Usuario\" SET \"Clave\" = %s WHERE \"UsuarioId\" = %s", (new_password, payload["id"]))

        # 4. Ejecución del UPDATE si hay datos
        if data_to_update:
            cursor.execute("SELECT \"DatosPersona\" FROM \"Usuario\" WHERE \"UsuarioId\" = %s", (payload["id"],))
            result_dp = cursor.fetchone()
            
            if result_dp:
                datos_persona_id = result_dp[0] 

                # Construcción dinámica del SQL
                set_clause = ", ".join([f"\"{key}\" = %s" for key in data_to_update.keys()])
                values = list(data_to_update.values()) # Usamos la función nativa list()
                values.append(datos_persona_id) 

                query = f"UPDATE \"DatosPersona\" SET {set_clause} WHERE \"DatosPersonaId\" = %s"
                cursor.execute(query, tuple(values))
        
        # 5. Si no hay datos texto pero hay archivos, también es válido.
        if not data_to_update and not files and not clave:
             raise MissingEntityData("No hay datos que actualizar")

        # 6. Manejo de Archivos
        if "DNI" in files:
            file = files["DNI"]
            if file.filename != "":
                if not Validations.is_pdf(file):
                    raise ValidationError("El documento DNI debe ser un PDF")
                have_dni = True
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"dni-{payload['id']}.pdf"))

        if "Foto" in files:
            file = files["Foto"]
            allowed_extensions = ["png", "jpg", "jpeg", "webp"]
            img_extension = get_format(file.filename)
            if file.filename != "":
                if img_extension not in allowed_extensions:
                    raise ValidationError("La foto debe ser una imagen válida")
                have_carnet = True
                img_converted = convert_to_webp(file)
                img = resize(img_converted, 500)
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"carnet-{payload['id']}.webp"))

        conn.commit()
        return Response(status=200)

    except Exception as err:
        conn.rollback()

        # Limpieza segura de archivos
        if payload and 'id' in payload:
            dni_path = Path(os.path.join(app.config['UPLOAD_FOLDER'], f"dni-{payload['id']}.pdf"))
            carnet_path = Path(os.path.join(app.config['UPLOAD_FOLDER'], f"carnet-{payload['id']}.webp"))

            if have_dni and dni_path.exists():
                dni_path.unlink()
            if have_carnet and carnet_path.exists():
                carnet_path.unlink()

        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@user_bp.route("/users/count", methods=["GET"])
def count():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        cursor.execute("SELECT COUNT(*) FROM \"Usuario\" WHERE \"Activo\" = TRUE;")
        count = cursor.fetchone()[0]
        return jsonify({"count": count}), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]    
    finally:
        cursor.close()

# --- NUEVA RUTA: VISTA DEL DASHBOARD PARA ADMINISTRADOR ---
@user_bp.route("/admin/dashboard/view", methods=["GET"])
def admin_dashboard_view():
    """
    Ruta para servir la vista principal del Dashboard del administrador.
    """
    try:
        return render_template("app/admin/dashboard/index.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
