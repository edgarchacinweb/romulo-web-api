from flask import Blueprint, jsonify, request, Response
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
        
        password = bcrypt.generate_password_hash(pwd, int(os.getenv("pwd_rounds"))).decode("utf8")

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
        elif not any(r in data["Rol"] for r in (Rol.PARENT.value, Rol.TEACHER.value)):
            raise ValidationError("Sólo puedes registrar un representante o un docente")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido")
        
        logger.debug("Validaciones realizadas")

        if not "Clave" in data or not data["Clave"]:
            password = Security.generate_password()
            logger.debug("Clave generada")
            # send_email(data["Email"], "Contraseña temporal", "temporal-password", password)
            # logger.debug("correo enviado")
        else:
            password = data["Clave"]


        user: Usuario = Usuario({
            "Email": data["Email"],
            "Clave": password,
            "Rol": Rol.PARENT if data["Rol"] == Rol.PARENT.value else Rol.TEACHER,
            "DatosPersonaId": data["DatosPersonaId"]
        })

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
    try:
        data = request.get_json()

        if not "Email" in data or not "Clave" in data:
            raise MissingEntityData("Falta correo electrónico o contraseña.")
        elif not Validations.is_password(data["Clave"]):
            raise ValidationError("La contraseña introducida no cumple con los parámetros de seguridad")
        
        auth = rep.get_by_email(data["Email"])
        if not auth:
            raise EntityNotFound("No se encontró a ningún usuario con ese correo electrónico")
        
        if not bcrypt.check_password_hash(auth.password, data["Clave"]):
            raise ValidationError("Contraseña inválida")
        
        auditory.create(Auditoria({
            "Accion": "Sesión",
            "Descripcion": "Inicio de sesión realizado",
            "Usuario": Usuario({
                "id": auth.id
            })
        }))

        return jsonify({"id": auth.id}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/get", methods=["GET"])
def get_user():
    try:
        payload = Security.verify_token(request.headers)
        
        if not payload:
            raise Unauthorized()

        if not Validations.is_uuid(payload["id"]):
            raise InvalidId(F"ID inválido: {id}")
        
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
            raise InvalidId(F"ID inválido: {id}")
        
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
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        offset = request.args.get("offset")
        limit = request.args.get("limit")
        if offset:        
            offset = int(offset)
        if limit:
            limit = int(limit)

        users = rep.list(offset, limit)
        
        if not users:
            raise EntityNotFound("No se encontraron usuarios registrados")

        for i in users:
            logger.info(i)

        return jsonify([u.to_dict() for u in users]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@user_bp.route("/user/get/rol/<int:ci>", methods=["DELETE"])
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
    try:
        payload = Security.verify_token(request.headers)

        data = request.get_json()

        if not data or "Password" not in data:
            raise ValidationError("Debes enviar la nueva contraseña")
        elif "RPassword" not in data:
            raise ValidationError("Debes enviar la contraseña de confirmación")
        
        password, rpassword = data["Password"], data["RPassword"]

        if (password != rpassword):
            raise ValidationError("Las contraseñas no coinciden")
        
        rep.update(payload["id"], {"Password": bcrypt.generate_password_hash(password, int(os.getenv("pwd_rounds"))).decode("utf8")})

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
