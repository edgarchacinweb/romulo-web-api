from flask import Blueprint, jsonify, request, Response
from database.Curso import CursoRep
from database.PeriodoEscolar import PeriodoEscolarRep
from models.Curso import Curso
from models.PeriodoEscolar import PeriodoEscolar
from models.Usuario import Rol
from models.CursoEstudiante import CursoEstudiante
from utils.exceptions import *
from utils.handler import exception_handler
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from database.connection import Connection  # <--- CORRECCIÓN 1: Importación añadida

rep = CursoRep()
logger = Logger()

course_bp = Blueprint("course", __name__)

@course_bp.route("/course/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data or any(key not in data for key in ("Grado", "Seccion", "Capacidad", "PeriodoEscolarId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_grade(data["Grado"]):
            raise ValidationError("El grado estudiantil introducido es inválido.")
        elif not Validations.is_section(data["Seccion"]):
            raise ValidationError("La sección introducida es inválida.")
        elif not Validations.is_capacity(data["Capacidad"]):
            raise ValidationError("La capacidad introducida de la sección tiene un formato inválido.")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("El identificador del periodo escolar es inválido.")

        curso = Curso({
            "Grado": data["Grado"],
            "Seccion": data["Seccion"],
            "Capacidad": data["Capacidad"],
            "PeriodoEscolar": PeriodoEscolar({
                "id": data["PeriodoEscolarId"]
            })
        })
        id = rep.create(curso)
        return jsonify({"id": id}), 201

    except Exception as e:
        ex = exception_handler(e)
        return jsonify(ex[0]), ex[1]
    
@course_bp.route("/course/get/<string:id>", methods=["GET"])
def get(id:str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"El identificador del curso es inválido")

        data = rep.get(id)

        return jsonify(data.to_dict()), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@course_bp.route("/course/get/literal")
def get_by_literal():
    try:
        grade = request.args.get("grade") or "1"
        section = request.args.get("section") or "1"

        if not Validations.is_grade(grade):
            raise ValidationError("El grado tiene un formato inválido")
        elif not Validations.is_section(section):
            raise ValidationError("La sección tiene un formato inválido")
        
        return rep.get_by_literal(grade, section)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/delete/<string:id>", methods=["DELETE"])
def delete(id:str = ""):
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not Validations.is_uuid(id):
            raise InvalidId(f"El identificador del curso es inválido")

        affected = rep.delete(id)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/update", methods=["PATCH"])
def update():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data or any(key not in data for key in ("CursoId", "Grado", "Seccion")):
            raise MissingEntityData("No se recibieron datos suficientes")

        if not Validations.is_uuid(data["CursoId"]):
            raise InvalidId(f"El ID introducido es inválido: {data['CursoId']}")
        elif not Validations.is_grade(data["Grado"]):
            raise ValidationError("El grado estudiantil introducido es inválido.")
        elif not Validations.is_section(data["Seccion"]):
            raise ValidationError("La sección introducida es inválida.")
        elif not Validations.is_capacity(data["Capacidad"]):
            raise ValidationError("La capacidad de la sección tiene un formato inválido.")

        course = Curso({
            "id": data["CursoId"],
            "Grado": data["Grado"],
            "Seccion": data["Seccion"],
            "Capacidad": data["Capacidad"],
        })
        affected = rep.update(course)

        if not affected:
            return Response(status=404)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/list", methods=["GET"])
def list():
    try:
        offset = request.args.get("offset")
        limit = request.args.get("limit")
        if offset:
            offset = int(offset)
        if limit:
            limit = int(limit)

        data = rep.list(limit, offset)
        return jsonify([d.to_dict() for d in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
@course_bp.route("/course/list/school_term", methods=["GET"])
@course_bp.route("/course/list/school_term/<string:id>", methods=["GET"])
def list_by_school_term(id:str = ""):
    try:
        if not id:
            id = PeriodoEscolarRep().get_latest().id

        if not Validations.is_uuid(id):
            raise InvalidId(f"El identificador del periodo escolar es invático: {id}")
        
        data = rep.get_all_by_school_term(id)
        courses = {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": []
        }

        for d in data:
            courses[str(d["Grado"])] += [d]

        return jsonify(courses), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/add", methods=["POST"])
def add():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if not data or any(key not in data for key in ("Grado", "Capacidad")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_grade(data["Grado"]):
            raise ValidationError("El grado del estudiante es inválido.")
        elif not Validations.is_capacity(data["Capacidad"]):
            raise ValidationError("La capacidad de la sección debe ser un número entero mayor a 15")

        course_id = rep.add(Curso({
            "Grado": data["Grado"],
            "Capacidad": data["Capacidad"]
        }))

        return jsonify({"id": course_id}), 201
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/add/many", methods=["POST"])
def add_many():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data: dict = request.get_json()
        courses = []

        for d in data.keys():
            for c in data[d]:
                if not Validations.is_grade(d):
                    raise ValidationError(f"El grado académico debe ser un número entero en el rango 1-5")
                elif not Validations.is_capacity(c):
                    raise ValidationError(f"La capacidad de la sección debe ser un número entero mayor a 15")
                courses.append(Curso({
                    "Grado": d,
                    "Capacidad": c
                }))

        rep.add_many(courses)
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/get_all", methods=["GET"])
def get_all():
    try:
        data = rep.get_all()
        return jsonify([d.to_dict() for d in data]), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/create/student_course", methods=["POST"])
def create_student_course():
    try:
        data = request.get_json()
        logger.debug(data, "DATA")

        if not data or not any(key in data for key in ("EstudianteId", "CursoId", "PeriodoEscolarId")):
            raise MissingEntityData("No se recibieron datos suficientes")
        if not Validations.is_uuid(data["EstudianteId"]):
            raise InvalidId("Identificador del estudiante inválido")
        elif not Validations.is_uuid(data["CursoId"]):
            raise InvalidId("Identificador del curso inválido")
        elif not Validations.is_uuid(data["PeriodoEscolarId"]):
            raise InvalidId("Identificador del período escolar inválido")
        
        model: CursoEstudiante = CursoEstudiante({
            "EstudianteId": data["EstudianteId"],
            "CursoId": data["CursoId"],
            "PeriodoEscolar": PeriodoEscolar({
                "id": data["PeriodoEscolarId"]
            })
        })

        rep.create_student_course(model)
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@course_bp.route("/course/sections", methods=["GET"])
@course_bp.route("/course/sections/<string:period_term_id>", methods=["GET"])
def get_max_sections(period_term_id:str = ""):
    try:
        if not period_term_id:
            period_term_id = PeriodoEscolarRep().get_latest().id
            
        if not Validations.is_uuid(period_term_id):
            raise InvalidId(f"El identificador del periodo escolar es inválido: {period_term_id}")
        
        return jsonify(rep.get_max_section(period_term_id)), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    
# --- CORRECCIÓN 2: Ruta segura para reinscripción ---
# --- RUTA CORREGIDA PARA REINSCRIPCIÓN (Sin columna Seccion) ---
@course_bp.route("/course/get_by_grade/<int:grado>", methods=["GET"])
def get_by_grade(grado):
    connection = Connection().get_connection()
    cursor = connection.cursor()
    try:
        # Añadimos seguridad básica
        payload = Security.verify_token(request.headers)
        if not payload: raise Unauthorized()

        # CAMBIO IMPORTANTE: Quitamos 'AND "Seccion" = 1'
        # Buscamos el primer curso disponible para ese grado.
        cursor.execute('SELECT "CursoId" FROM "Curso" WHERE "Grado" = %s LIMIT 1;', (grado,))
        row = cursor.fetchone()
        
        if row:
            return jsonify({"CursoId": row[0]}), 200
        else:
            return jsonify({"message": f"No se encontró un curso registrado para {grado}° Año"}), 404
            
    except Exception as err:
        connection.rollback() # Vital para evitar bloqueos
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()