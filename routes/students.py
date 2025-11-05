from flask import Blueprint, jsonify, request, Response
from database.Estudiante import EstudianteRep
from database.DatosPersona import DatosPersonaRep
from database.Usuario import Usuario, UsuarioRep
from database.Auditoria import Auditoria, AuditoriaRep
from database.Curso import CursoRep, Curso
from database.Clase import ClaseRep, Clase
from models.Estudiante import Estudiante
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from models.Usuario import Rol
from models.DatosPersona import DatosPersona
from models.Curso import Curso
from utils.handler import exception_handler
from datetime import datetime

rep = EstudianteRep()
logger = Logger()

student_bp = Blueprint("student", __name__)

@student_bp.route("/students/create", methods=["POST"])
def create():
    try:
        data = request.get_json()

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "RepresentanteId")):
            raise MissingEntityData("No se recibieron datos suficientes")

        if not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_uuid(data["RepresentanteId"]):
            raise InvalidId("El ID del representante es inválido.")

        data["Activo"] = True
        estudiante = Estudiante({
            "FechaNacimiento": data["FechaNacimiento"],
            "DatosPersonaId": data["DatosPersonaId"],
            "RepresentanteId": data["RepresentanteId"]
        })
        id = rep.create(estudiante)

        parent_id = UsuarioRep().get_by_people_id(data["RepresentanteId"])

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": "Registro de datos del estudiante",
            "Usuario": Usuario({
                "id": parent_id
            })
        }))

        return jsonify({"id": id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/create/parent_ci", methods=["POST"])
def create_parent_by_ci():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "CedulaRepresentante", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_ci(data["CedulaRepresentante"]):
            raise InvalidId("El ID del representante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        data["Activo"] = True
        estudiante = Estudiante({
            "FechaNacimiento": datetime.strptime(data["FechaNacimiento"], "%Y-%m-%d").date(),
            "DatosPersona": DatosPersona({"id": data["DatosPersonaId"]}),
            "Representante": DatosPersona({"Cedula": data["CedulaRepresentante"]}),
            "Curso": Curso({"id": data["CursoId"]})
        })
        rep.create_by_ci(estudiante)
        return Response(status=201)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

    
@student_bp.route("/students/get/<string:id>", methods=["GET"])
def get(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or not payload["role"] in (Rol.ADMIN.name, Rol.PARENT.name):
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        estudiante = rep.get(id)

        if estudiante == None:
            raise EntityNotFound(f"No se encontró ningún estudiante con ese identificador")

        return jsonify(estudiante.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/list", methods=["GET"])
def list():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        offset = None
        limit = None

        if request.args.get("offset") != None:
            offset = int(request.args.get("offset"))
        if request.args.get("limit") != None:
            limit = int(request.args.get("limit"))

        students = rep.list(offset, limit)

        if not students:
            raise EntityNotFound("No se encontraron estudiantes registrados")

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/delete/<string:id>", methods=["DELETE"])
def delete(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        affected = rep.delete(id)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@student_bp.route("/students/update/<string:id>", methods=["PUT"])
def update(id: str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_uuid(id):
            raise InvalidId(f"ID inválido: {id}")

        data = request.get_json()

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "RepresentanteId", "CursoId", "Activo")):
            raise MissingEntityData("No se recibieron datos suficientes")

        if not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_uuid(data["RepresentanteId"]):
            raise InvalidId("El ID del representante es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")
        
        student = Estudiante(data)
        affected = rep.update(student)

        if not affected:
            raise EntityUpdateError("No se pudo actualizar los datos del estudiante")
        
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get_all", methods=["GET"])
def get_all():
    try:
        students = rep.get_all()
        logger.debug(students)
        return jsonify(students), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/create/parent", methods=["POST"])
def create_parent():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        
        data = request.get_json()
        
        if not Validations.is_ci(f"{data['CedulaRepresentante']}"):
            raise ValidationError(f"Cédula de identidad del representante inválida")
        
        parent_id = DatosPersonaRep().get_by_ci(data["CedulaRepresentante"])

        if not data or any(key not in data for key in ("FechaNacimiento", "DatosPersonaId", "CursoId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_date(data["FechaNacimiento"]):
            raise ValidationError("La fecha de nacimiento introducida es inválida.")
        elif not Validations.is_uuid(data["DatosPersonaId"]):
            raise InvalidId("El ID de la persona es inválido.")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("El ID del curso es inválido.")

        student = Estudiante({
            "FechaNacimiento": data["FechaNacimiento"],
            "DatosPersonaId": data["DatosPersonaId"],
            "RepresentanteId": parent_id,
            "CursoId": data["CursoId"],
            "Activo": True
        })


        student_id = rep.create(student)

        if not student_id:
            raise InsertEntityError("Ocurrido un error al intentar registrar al estudiante")

        return jsonify({"id": student_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list/parent/<string:parent_id>", methods=["GET"])
def list_by_parent(parent_id: str = ""):
    try:
        if not Validations.is_uuid(parent_id):
            raise InvalidId(f"ID inválido: {parent_id}")

        students = rep.list_by_parent(parent_id)

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/list_by_class/<string:classroom_id>", methods=["GET"])
def list_by_class(classroom_id: str):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        if not Validations.is_uuid(classroom_id):
            raise InvalidId(f"El identificador de la clase es inválido")
        
        students = rep.list_by_class(Clase({"id": classroom_id}))

        return jsonify([s.to_dict() for s in students]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/get/by_people/<string:id>", methods=["GET"])
def get_by_ci(id: str):
    try:
        data = rep.get_by_people(id);
        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@student_bp.route("/students/count", methods=["GET"])
def count():
    try:
        return jsonify({"count": rep.count()}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
