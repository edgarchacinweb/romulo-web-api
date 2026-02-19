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

# --- VALIDACIÓN DE SEGURIDAD PARA CÉDULA ---
def validar_reglas_cedula(cedula):
    cedula_str = str(cedula).strip().upper()
    
    # 1. CASO CÉDULA ESCOLAR (11 o 12 Caracteres)
    
    # A. Escolar Venezolana (V Implícita): 11 dígitos numéricos
    # Formato: Orden(1) + Año(2) + Madre(8) = 11
    # Al guardarse como número puro, el sistema al mostrarla le agregará "V-" correctamente.
    if len(cedula_str) == 11 and cedula_str.isdigit():
        return True 

    # B. Escolar Extranjera (E Explícita): E + 11 dígitos = 12
    # Formato: E + Orden(1) + Año(2) + Madre(8) = 12
    # Aquí sí permitimos la letra E para que el sistema sepa que es extranjero.
    if len(cedula_str) == 12:
        if cedula_str.startswith("E") and cedula_str[1:].isdigit():
             return True
        # Si tiene 12 caracteres pero no empieza con E, rechazamos para evitar inconsistencias.

    # 2. CASO CÉDULA REGULAR (7-9 Caracteres)
    # Verificamos si es extranjero (Empieza por E)
    es_extranjero = cedula_str.startswith("E")
    
    # Validamos solo la parte numérica
    numero_a_validar = cedula_str[1:] if es_extranjero else cedula_str

    if not numero_a_validar.isdigit():
        raise ValidationError("La cédula regular debe contener solo números (después del prefijo si aplica)")
    
    if numero_a_validar.startswith("0"):
        raise ValidationError("La cédula no puede comenzar con 0")
        
    length = len(numero_a_validar)
    if length < 7 or length > 9:
        raise ValidationError("La cédula regular debe tener entre 7 y 9 dígitos")
        
    if int(numero_a_validar) <= 1000000:
        raise ValidationError("La cédula debe ser mayor a 1.000.000")
        
    return True

@people_bp.route("/people/create", methods=["POST"])
def create():
    try:
        data = request.get_json()
        
        # Validación de reglas de negocio
        if "Cedula" in data:
            validar_reglas_cedula(data["Cedula"])

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
            try:
                # Intentamos buscar tal cual viene (string)
                person_response = rep.get_by_ci(person.ci, exception=False)
            except:
                person_response = None

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
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        offset = request.args.get("offset", 0)
        limit = request.args.get("limit", 100)

        query = """
            SELECT dp."DatosPersonaId", dp."Nombre", dp."Apellido", dp."Sexo", dp."Cedula", 
                   dp."Direccion", dp."Telefono", dp."Ocupacion", u."Email", u."UsuarioId"
            FROM "DatosPersona" dp
            INNER JOIN "Usuario" u ON u."DatosPersona" = dp."DatosPersonaId"
            WHERE u."Rol" = 'representante'
            ORDER BY dp."Nombre" ASC
            LIMIT %s OFFSET %s;
        """
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "UsuarioId": row[9],
                "Email": row[8],
                "DatosPersona": {
                    "DatosPersonaId": row[0],
                    "Nombre": row[1],
                    "Apellido": row[2],
                    "Sexo": row[3],
                    "Cedula": row[4],
                    "Direccion": row[5] if row[5] else None,
                    "Telefono": row[6] if row[6] else None,
                    "Ocupacion": row[7] if row[7] else None
                },
                "Usuario": {
                    "Email": row[8],
                    "UsuarioId": row[9]
                }
            })

        return jsonify(result), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

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
        clean_id = id.strip()
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        elif not Validations.is_uuid(clean_id):
            raise InvalidId(f"ID de representante inválido: {clean_id}")

        data_dict = request.get_json()

        if not data_dict:
            raise MissingEntityData("No hay datos que actualizar")
            
        if "Cedula" in data_dict:
            validar_reglas_cedula(data_dict["Cedula"])

        personData = DatosPersona(data_dict)
        personData.id = clean_id
        
        if "Direccion" in data_dict:
            personData.direccion = data_dict["Direccion"]
        if "Ocupacion" in data_dict:
            personData.ocupacion = data_dict["Ocupacion"]
        if "Telefono" in data_dict:
            personData.phone = data_dict["Telefono"]

        affected = rep.update(personData)

        if "Email" in data_dict:
            if not Validations.is_email(data_dict["Email"]):
                raise ValidationError("El formato del correo electrónico es inválido")
            
            conn = Connection().get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE "Usuario" SET "Email" = %s WHERE "DatosPersonaId" = %s', (data_dict["Email"], clean_id))
            conn.commit()
            cursor.close() 
            affected = True

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@people_bp.route("/people/get_parent/ci/<string:ci>", methods=["GET"])
def get_by_ci(ci: str):
    try:
        data = rep.get_by_ci(ci)
        logger.debug("data", data.to_dict())
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]