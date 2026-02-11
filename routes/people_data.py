from flask import Blueprint, request, jsonify, Response
from models.DatosPersona import DatosPersona
from models.Usuario import Rol
from database.DatosPersona import DatosPersonaRep
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from utils.exceptions import *
from utils.handler import exception_handler
from database.connection import Connection

people_bp = Blueprint("people", __name__)
logger = Logger()
rep = DatosPersonaRep()

@people_bp.route("/people/create", methods=["POST"])
def create():
    try:
        data = request.get_json()
        person = DatosPersona({
            "Nombre": data["Nombre"],
            "Apellido": data["Apellido"],
            "Sexo": data["Sexo"],
            "Cedula": data["Cedula"],
        })

        if "Telefono" in data:
            person.phone = data["Telefono"]

        if "Direccion" in data and "Ocupacion" in data:
            person.direccion = data["Direccion"]
            person.ocupacion = data["Ocupacion"]

        if person.ci:
            person_response = rep.get_by_ci(int(person.ci), exception=False)

            if person_response and person_response.id:
                person.id = person_response.id
                DatosPersonaid = rep.update(person)
                return jsonify({"id": person_response.id}), 200

        DatosPersonaid = rep.create(person)
        
        if DatosPersonaid != None:
            return jsonify({"id": DatosPersonaid}), 201
        else:
           raise InsertEntityError("No se pudo insertar el registro en la base de datos")
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@people_bp.route("/people/get")
@people_bp.route("/people/get/<string:id>", methods=["GET"])
def get(id:str = None):
    try:
        payload = Security.verify_token(request.headers)

        if not payload:
            raise Unauthorized()
        elif not Validations.is_uuid(payload["id"]) and (id != None or not Validations.is_uuid(id)):
            raise ValidationError(f"ID inválido: {id}")
        
        if payload["role"] == Rol.ADMIN.name:
            user = id
        else:
            user = rep.get_by_user(payload["id"])
            if not user:
                raise Unauthorized()

        data = rep.get(user)
        if data == None:
            raise EntityNotFound(f"No se encontraron datos con el ID: {id}")
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@people_bp.route("/people/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        offset = request.args.get("offset")
        limit = request.args.get("limit")

        if offset != None:
            offset = int(offset)
        if limit != None:
            limit = int(limit)

        data = rep.list(limit, offset)

        if data == None or len(data) == 0:
            raise EntityNotFound("No hay datos disponibles")
        
        return jsonify([d.to_dict() for d in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@people_bp.route("/people/delete/<string:id>", methods=["DELETE"])
def delete(id):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        affected = rep.delete(id)

        if not affected:
            raise EntityDeleteError("Ocurrió un error al intentar eliminar los datos")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@people_bp.route("/people/update/<string:id>", methods=["PATCH"])
def update(id: str = ""):
    try:
        # 1. Limpiamos el ID
        clean_id = id.strip()
        
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        # 2. Validamos el ID. OJO: Si falla aquí, revisa que clean_id no sea "undefined"
        elif not Validations.is_uuid(clean_id):
            raise InvalidId(f"ID de representante inválido: {clean_id}")

        data_dict = request.get_json()

        if not any(key in data_dict for key in ("Nombre", "Apellido", "Sexo", "Cedula", "Telefono", "Email")):
            raise MissingEntityData("No hay datos que actualizar")

        # 3. Actualizar Persona
        personData = DatosPersona(data_dict)
        personData.id = clean_id
        affected = rep.update(personData)

        # 4. Actualizar Email (CORREGIDO: Sin cerrar conexión manualmente)
        if "Email" in data_dict:
            if not Validations.is_email(data_dict["Email"]):
                raise ValidationError("El formato del correo electrónico es inválido")
            
            # Abrimos cursor, ejecutamos y hacemos commit.
            # NO cerramos 'conn' aquí para evitar matar la conexión del pool.
            conn = Connection().get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE "Usuario" SET "Email" = %s WHERE "DatosPersonaId" = %s', (data_dict["Email"], clean_id))
            conn.commit()
            cursor.close() 
            # Eliminamos conn.close() para evitar el Error 500

        if not affected and "Email" not in data_dict:
            raise EntityUpdateError("Ocurrió un error en la base de datos o no hubo cambios")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@people_bp.route("/people/get_parent/ci/<string:ci>", methods=["GET"])
def get_by_ci(ci: str):
    try:
        if not Validations.is_ci(ci):
            raise ValidationError(f"Cedula de identidad inválida")

        data = rep.get_by_ci(ci)
        logger.debug("data", data.to_dict())
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]