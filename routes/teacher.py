from flask import Blueprint, jsonify, request, Response
from database.Docente import DocenteRep
from models.Docente import Docente
from models.DatosPersona import DatosPersona
from models.Materia import Materia
from utils.exceptions import *
from utils.validations import Validations
from utils.logger import Logger
from utils.Security import Security
from models.Usuario import Usuario, Rol
from models.Auditoria import Auditoria
from utils.handler import exception_handler
from database.Auditoria import AuditoriaRep
from database.connection import Connection
from utils.config import bcrypt  # <-- Importamos flask_bcrypt igual que en users.py
from os import getenv

rep = DocenteRep()
logger = Logger()
auditory = AuditoriaRep()

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/teacher/create", methods=["POST"])
def create_teacher():
    conn = Connection().get_connection()
    cursor = conn.cursor()

    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if "Nombre" not in data or not data["Nombre"]:
            raise MissingEntityData("El nombre del docente es requerido")
        elif not Validations.is_name(data["Nombre"]):
            raise ValidationError("El nombre del docente tiene un formato incorrecto")
        elif "Apellido" not in data or not data["Apellido"]:
            raise MissingEntityData("El apellido del docente es requerido")
        elif not Validations.is_lastname(data["Apellido"]):
            raise ValidationError("El apellido del docente tiene un formato incorrecto")
        elif "Sexo" not in data or not data["Sexo"]:
            raise MissingEntityData("El sexo del docente es requerido")
        elif not Validations.is_gender(data["Sexo"]):
            raise ValidationError("El sexo del docente tiene un formato incorrecto")
        elif "Cedula" not in data or not data["Cedula"]:
            raise MissingEntityData("La cédula del docente es requerida")
        elif not (str(data["Cedula"]).isdigit() and 5 <= len(str(data["Cedula"]).strip()) <= 8):
            raise ValidationError("La cédula del docente debe tener entre 5 y 8 dígitos numéricos")
        elif not (3000000 < int(data["Cedula"]) < 29000000):
            raise ValidationError("La cédula del docente debe ser estrictamente mayor a 3.000.000 y menor a 29.000.000")
        elif len(set(str(data["Cedula"]).strip())) == 1 or str(data["Cedula"]).strip() in ["1234567", "12345678", "8765432", "87654321", "2345678", "23456789", "9876543", "98765432", "0123456", "01234567", "7654321", "76543210"]:
            raise ValidationError("La cédula del docente presenta un formato inválido por secuencia repetitiva")
        elif "Telefono" not in data or not data["Telefono"]:
            raise MissingEntityData("El teléfono del docente es requerido")
        elif not Validations.is_phone(data["Telefono"]):
            raise ValidationError("El teléfono del docente debe tener un prefijo válido y exactamente 7 dígitos numéricos (Ej: 0412-1234567)")
        elif data["Telefono"].split("-")[1] == "0000000" or len(set(data["Telefono"].split("-")[1])) == 1:
            raise ValidationError("El teléfono del docente presenta un formato inválido (número iterativo o nulo)")
        elif "Ocupacion" not in data or not data["Ocupacion"]:
            raise MissingEntityData("La ocupación del docente es requerida")
        elif "Direccion" not in data or not data["Direccion"]:
            raise MissingEntityData("La dirección del docente es requerida")
        elif "Email" not in data or not data["Email"]:
            raise MissingEntityData("El email del docente es requerido")
        elif not Validations.is_email(data["Email"]) or not data["Email"].lower().endswith(("@gmail.com", "@hotmail.com", "@yahoo.com", "@outlook.com")):
            raise ValidationError("El correo electrónico del docente debe ser @gmail.com, @hotmail.com, @yahoo.com o @outlook.com")
        elif "Horas" not in data or not data["Horas"]:
            raise MissingEntityData("Las horas del docente son requeridas")
        elif not Validations.is_teacher_hours(data["Horas"]):
            raise ValidationError("Las horas del docente tienen un formato incorrecto")
        elif "Materias" not in data or len(data["Materias"]) == 0:
            raise MissingEntityData("Las materias del docente son requeridas")
        else:
            for materia in data["Materias"]:
                if not Validations.is_uuid(materia):
                    raise ValidationError("El ID de la materia es inválido")

        # Creando registro de datos del docente
        if "DatosPersonaId" not in data:
            cursor.execute('SELECT "DatosPersonaId" FROM "DatosPersona" WHERE "Cedula" = %s', (str(data["Cedula"]).strip(),))
            existing_dp = cursor.fetchone()
            if existing_dp:
                id_datos_persona = existing_dp[0]
                cursor.execute(
                    """
                    UPDATE "DatosPersona" SET "Nombre"=%s, "Apellido"=%s, "Sexo"=%s, "Telefono"=%s, "Ocupacion"=%s, "Direccion"=%s
                    WHERE "DatosPersonaId"=%s
                    """,
                    (data["Nombre"], data["Apellido"], data["Sexo"], data["Telefono"], data["Ocupacion"], data["Direccion"], id_datos_persona)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO "DatosPersona" ("Nombre", "Apellido", "Sexo", "Cedula", "Telefono", "Ocupacion", "Direccion")
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING "DatosPersonaId"
                    """,
                    (data["Nombre"], data["Apellido"], data["Sexo"], data["Cedula"], data["Telefono"], data["Ocupacion"], data["Direccion"])
                )

                id_datos_persona = cursor.fetchone()[0]
        else:
            id_datos_persona = data["DatosPersonaId"]
        
        if not id_datos_persona:
            raise EntityNotFound("Error al registrar los datos del docente")

        # --- CORRECCIÓN EN LA ENCRIPTACIÓN DE LA CONTRASEÑA ---
        # Ahora usamos flask_bcrypt y lo decodificamos a string (texto) igual que los representantes
        pwd = bcrypt.generate_password_hash(f"V#{data['Cedula']}", int(getenv("pwd_rounds"))).decode("utf8")
        # --------------------------------------------------------

        # Creando registro de docente
        cursor.execute(
            """
            INSERT INTO "Docente" ("HorasAcademicas", "DatosPersonaId")
            VALUES (%s, %s) RETURNING "DocenteId"
            """,
            (data["Horas"], id_datos_persona)
        )

        id_docente = cursor.fetchone()[0]
        
        if not id_docente:
            raise EntityNotFound("Error al registrar el docente")

        # Vinculando materias al docente
        for materia in data["Materias"]:
            cursor.execute(
                """
                INSERT INTO "DocenteMateria" ("DocenteId", "MateriaId")
                VALUES (%s, %s)
                """,
                (id_docente, materia)
            )

        if not cursor.rowcount:
            raise EntityNotFound("Error al vincular las materias al docente")

        # Creando registro de usuario
        cursor.execute(
            """
            INSERT INTO "Usuario" ("Email", "Clave", "Rol", "DatosPersona")
            VALUES (%s, %s, %s, %s) RETURNING "UsuarioId"
            """,
            (data["Email"], pwd, Rol.TEACHER.value, id_datos_persona)
        )

        id_usuario = cursor.fetchone()[0]

        if not id_usuario:
            raise EntityNotFound("Error al registrar el usuario del docente")

        # Registrando auditoría
        cursor.execute(
            """
            INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion")
            VALUES (%s, %s, %s) RETURNING "AuditoriaId"
            """,
            (payload["id"], f"Docente {data['Nombre']} {data['Apellido']} registrado exitosamente", "Registro")
        )

        id_auditoria = cursor.fetchone()[0]

        if not id_auditoria:
            raise EntityNotFound("Error al registrar la auditoría")

        conn.commit()

        return jsonify({"DocenteId": id_docente}), 201
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/remove_subject", methods=["DELETE"])
def remove_subject():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()

        if any(key not in data for key in ("Cedula", "Materia")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_ci(data["Cedula"]):
            raise ValidationError("El número de Cédula del docente tiene un formato incorrecto")
        elif not Validations.is_subject(data["Materia"]):
            raise InvalidId("El nombre de la materia tiene un formato inválido")

        rep.remove_subject(data["Cedula"], data["Materia"])

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@teacher_bp.route("/teacher/list", methods=["GET"])
def list():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name and payload["role"] != Rol.PARENT.name:
            raise Unauthorized()

        cursor.execute(
            """
            SELECT DISTINCT * FROM "Docente" AS d
            INNER JOIN "DatosPersona" AS dp ON d."DatosPersonaId"=dp."DatosPersonaId"
            INNER JOIN "Usuario" AS u ON u."DatosPersona"=d."DatosPersonaId"
            WHERE u."Rol" = %s
            ORDER BY d."Activo" DESC, d."FechaCreacion" DESC;
            """,
            (Rol.TEACHER.value,)
        )

        teachers = cursor.fetchall()

        if not teachers or len(teachers) == 0:
            return jsonify([]), 200

        cursor.execute(
            """
            SELECT dm."DocenteId", m."MateriaId", m."Nombre" FROM "DocenteMateria" AS dm INNER JOIN "Materia" AS m ON dm."MateriaId"=m."MateriaId";
            """
        )

        subjects = cursor.fetchall()

        return jsonify([{
            "DocenteId": t[0],
            "HorasAcademicas": t[2],
            "Activo": t[3],
            "DatosPersona": {
                "DatosPersonaId": t[5],
                "Nombre": t[6],
                "Apellido": t[7],
                "Sexo": t[8],
                "Cedula": t[9],
                "Telefono": t[10],
                "Direccion": t[11],
                "Ocupacion": t[12],
            },
            "Usuario": {
                "UsuarioId": t[15],
                "Email": t[16]
            },
            "Materias": [{"MateriaId": s[1], "Nombre": s[2]} for s in filter(lambda s: s[0] == t[0], subjects)]
        } for t in teachers]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/remove/<string:id>", methods=["DELETE"])
def remove(id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        if not id or not Validations.is_uuid(id):
            raise ValidationError("El ID del docente es inválido")

        cursor.execute(
            """
            SELECT "DatosPersonaId" FROM "Docente" WHERE "DocenteId"=%s;
            """,
            (id,)
        )

        id_datos_persona = cursor.fetchone()[0]

        if not id_datos_persona:
            raise EntityNotFound("El docente no existe")

        cursor.execute(
            """
            SELECT "Nombre", "Apellido" FROM "DatosPersona" WHERE "DatosPersonaId"=%s;
            """,
            (id_datos_persona,)
        )

        nombre, apellido = cursor.fetchone()

        cursor.execute(
            """
            DELETE FROM "Horario" WHERE "DocenteId"=%s;
            DELETE FROM "DocenteMateria" WHERE "DocenteId"=%s;
            DELETE FROM "Docente" WHERE "DocenteId"=%s;
            DELETE FROM "DatosPersona" WHERE "DatosPersonaId"=%s;
            INSERT INTO "Auditoria" ("UsuarioId", "Descripcion", "Accion") VALUES (%s, %s, %s);
            DELETE FROM "Usuario" WHERE "DatosPersona"=%s;
            """,
            (id, id, id_datos_persona, payload["id"], f"Docente {nombre} {apellido} eliminado exitosamente", "Eliminar", id_datos_persona)
        )

        conn.commit()
        return Response(status=204)
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/count", methods=["GET"])
def count():
    try:
        count = rep.count()
        return jsonify({"count": count}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

# Obtener ID del docente a través de su token de autenticación
@teacher_bp.route("/teacher/get", methods=["GET"])
def get_teacher_id():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        cursor.execute(
            """
            SELECT d."DocenteId" FROM "Usuario" AS u INNER JOIN "Docente" AS d ON d."DatosPersonaId"=u."DatosPersona" WHERE u."UsuarioId"=%s;
            """,
            (payload["id"],)
        )

        id_docente = cursor.fetchone()[0]

        if not id_docente:
            raise EntityNotFound("El docente no existe")

        return jsonify({"DocenteId": id_docente}), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/update/<string:teacher_id>", methods=["PUT"])
def update(teacher_id):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()

        data = request.get_json()
        admin_id = payload["id"]

        if any(key not in data for key in ("Cedula", "Nombre", "Apellido", "Sexo", "Telefono", "Direccion", "Ocupacion", "Horas", "Materias", "Email")):
            raise MissingEntityData("No se recibieron datos suficientes")
        elif not Validations.is_email(data["Email"]) or not data["Email"].lower().endswith(("@gmail.com", "@hotmail.com", "@yahoo.com", "@outlook.com")):
            raise ValidationError("El correo electrónico del docente debe ser @gmail.com, @hotmail.com, @yahoo.com o @outlook.com")
        elif not (str(data["Cedula"]).isdigit() and 5 <= len(str(data["Cedula"]).strip()) <= 8):
            raise ValidationError("El número de Cédula del docente debe tener entre 5 y 8 dígitos numéricos")
        elif not (3000000 < int(data["Cedula"]) < 29000000):
            raise ValidationError("La cédula del docente debe ser estrictamente mayor a 3.000.000 y menor a 29.000.000")
        elif len(set(str(data["Cedula"]).strip())) == 1 or str(data["Cedula"]).strip() in ["1234567", "12345678", "8765432", "87654321", "2345678", "23456789", "9876543", "98765432", "0123456", "01234567", "7654321", "76543210"]:
            raise ValidationError("La cédula del docente presenta un formato inválido por secuencia repetitiva")
        elif not Validations.is_name(data["Nombre"]):
            raise ValidationError("El nombre del docente tiene un formato incorrecto")
        elif not Validations.is_name(data["Apellido"]):
            raise ValidationError("El apellido del docente tiene un formato incorrecto")
        elif data["Sexo"] not in ["Masculino", "Femenino"]:
            raise ValidationError("El sexo del docente tiene un formato incorrecto")
        elif not Validations.is_phone(data["Telefono"]):
            raise ValidationError("El teléfono del docente debe tener un prefijo válido y exactamente 7 dígitos numéricos (Ej: 0412-1234567)")
        elif data["Telefono"].split("-")[1] == "0000000" or len(set(data["Telefono"].split("-")[1])) == 1:
            raise ValidationError("El teléfono del docente presenta un formato inválido (número iterativo o nulo)")
        elif not Validations.is_address(data["Direccion"]):
            raise ValidationError("La dirección del docente tiene un formato incorrecto")
        elif not Validations.is_occupation(data["Ocupacion"]):
            raise ValidationError("La ocupación del docente tiene un formato incorrecto")
        elif int(data["Horas"]) < 20 or int(data["Horas"]) > 40:
            raise ValidationError("Las horas del docente deben estar entre 20 y 40")
        elif data["Activo"] not in [True, False]:
            raise ValidationError("El estado del docente tiene un formato incorrecto")

        cursor.execute(
            """
            SELECT "DatosPersonaId" FROM "Docente" WHERE "DocenteId"=%s;
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()
        if result is None:
            raise EntityNotFound("El docente no existe")

        id_datos_persona = result[0]

        if not id_datos_persona:
            raise EntityNotFound("El docente no existe")

        # Actualizar datos personales
        cursor.execute(
            """
            UPDATE "DatosPersona" SET "Cedula"=%s, "Nombre"=%s, "Apellido"=%s, "Sexo"=%s, "Telefono"=%s, "Direccion"=%s, "Ocupacion"=%s WHERE "DatosPersonaId"=%s;
            """,
            (data["Cedula"], data["Nombre"], data["Apellido"], data["Sexo"], data["Telefono"], data["Direccion"], data["Ocupacion"], id_datos_persona)
        )

        # Actualizar horas académicas y estado
        cursor.execute(
            """
            UPDATE "Docente" SET "HorasAcademicas"=%s, "Activo"=%s WHERE "DocenteId"=%s;
            """,
            (data["Horas"], data["Activo"], teacher_id)
        )

        # Eliminar las materias que no estén en la nueva lista
        if data["Materias"]:
            cursor.execute(
                """
                DELETE FROM "DocenteMateria" WHERE "DocenteId"=%s AND "MateriaId" NOT IN %s;
                """,
                (teacher_id, tuple(data["Materias"]))
            )
        else:
            cursor.execute(
                """
                DELETE FROM "DocenteMateria" WHERE "DocenteId"=%s;
                """,
                (teacher_id,)
            )

        # Agregar las materias que aparecen en la lista de materias pero no existen en la tabla DocenteMateria
        cursor.execute(
            """
            SELECT "MateriaId" FROM "DocenteMateria" WHERE "DocenteId"=%s;
            """,
            (teacher_id,)
        )

        materias_existentes = [row[0] for row in cursor.fetchall()]
        materias_a_agregar = []

        for materia in data["Materias"]:
            if materia not in materias_existentes:
                materias_a_agregar.append((teacher_id, materia))

        if materias_a_agregar:
            cursor.executemany(
                """
                INSERT INTO "DocenteMateria" ("DocenteId", "MateriaId") VALUES (%s, %s);
                """,
                materias_a_agregar
            )

        # Actualizar el correo electrónico
        cursor.execute(
            """
            UPDATE "Usuario" SET "Email"=%s WHERE "DatosPersona"=%s;
            """,
            (data["Email"], id_datos_persona)
        )

        # Registrar en auditorías
        cursor.execute(
            """
            INSERT INTO "Auditoria" ("Accion", "Descripcion", "UsuarioId") VALUES (%s, %s, %s);
            """,
            ("Actualización", f"Datos del docente {data['Nombre']} {data['Apellido']} actualizados", admin_id)
        )

        conn.commit()
        return jsonify({"DocenteId": teacher_id}), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/subjects", methods=["GET"])
def get_subjects():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        # Obtener el ID del docente
        cursor.execute(
            """
            SELECT d."DocenteId" FROM "Usuario" AS u INNER JOIN "Docente" AS d ON d."DatosPersonaId"=u."DatosPersona" WHERE u."UsuarioId"=%s;
            """,
            (payload["id"],)
        )

        teacher_id = cursor.fetchone()[0]

        if not teacher_id:
            raise EntityNotFound("No se encontró el docente")

        cursor.execute(
            """
            SELECT dm."DocenteId", m."MateriaId", m."Nombre" FROM "DocenteMateria" AS dm INNER JOIN "Materia" AS m ON dm."MateriaId"=m."MateriaId" WHERE dm."DocenteId"=%s;
            """,
            (teacher_id,)
        )

        subjects = cursor.fetchall()

        return jsonify([{"MateriaId": s[1], "Nombre": s[2]} for s in subjects]), 200
    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@teacher_bp.route("/teacher/assignments", methods=["GET"])
def get_assignments():
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        payload = Security.verify_token(request.headers)
        if not payload or payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()

        # Obtener el Periodo Escolar Activo
        cursor.execute("SELECT \"PeriodoEscolarId\" FROM \"PeriodoEscolar\" WHERE \"Activo\"=true ORDER BY \"FechaInicio\" DESC LIMIT 1;")
        periodo_row = cursor.fetchone()
        if not periodo_row:
            return jsonify([]), 200
            
        periodo_id = periodo_row[0]

        # Obtener el ID del docente
        cursor.execute(
            """
            SELECT d."DocenteId" FROM "Usuario" AS u INNER JOIN "Docente" AS d ON d."DatosPersonaId"=u."DatosPersona" WHERE u."UsuarioId"=%s;
            """,
            (payload["id"],)
        )
        teacher_row = cursor.fetchone()
        if not teacher_row:
            raise EntityNotFound("No se encontró el docente")
            
        teacher_id = teacher_row[0]

        # Traer Grados, Secciones y Materias únicas asociadas al docente en el periodo activo
        cursor.execute(
            """
            SELECT DISTINCT h."CursoId", c."Grado", h."Seccion", h."MateriaId", m."Nombre" 
            FROM "Horario" AS h 
            INNER JOIN "Curso" AS c ON h."CursoId"=c."CursoId" 
            INNER JOIN "Materia" AS m ON h."MateriaId"=m."MateriaId" 
            WHERE h."DocenteId"=%s AND h."PeriodoEscolarId"=%s
            ORDER BY c."Grado", h."Seccion", m."Nombre";
            """,
            (teacher_id, periodo_id)
        )

        rows = cursor.fetchall()
        
        return jsonify([{
            "CursoId": r[0],
            "Grado": r[1],
            "Seccion": r[2],
            "MateriaId": r[3],
            "MateriaNombre": r[4]
        } for r in rows]), 200

    except Exception as err:
        conn.rollback()
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()
