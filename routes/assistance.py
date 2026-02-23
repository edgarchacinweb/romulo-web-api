from flask import Blueprint, jsonify, request, Response
from utils.handler import exception_handler
from utils.helpers import number_to_letter
from utils.Security import Security
from utils.logger import Logger
from models.Usuario import Rol, Usuario
from utils.exceptions import Unauthorized
from database.Asistencia import AsistenciaRep, Asistencia
from database.Auditoria import AuditoriaRep, Auditoria
from database.Clase import ClaseRep
from utils.validations import Validations
from utils.exceptions import ValidationError

logger = Logger()
rep = AsistenciaRep()

assistance_bp = Blueprint("assistance", __name__)


@assistance_bp.route("/assistance/create", methods=["POST"])
def create():
    try:
        payload = Security.verify_token(request.headers)

        if not payload or payload["role"] != Rol.ADMIN.name and payload["role"] != Rol.TEACHER.name:
            raise Unauthorized()
        
        data = request.get_json()

        if not Validations.is_uuid(data["ClaseId"]):
            raise ValidationError("El ID de la clase es inválido")
        
        # --- NUEVA LÓGICA PARA JUSTIFICACIONES ---
        # Obtenemos la lista. Si el front por alguna razón falla y no la envía, ponemos un valor por defecto para no quebrar el backend
        justificaciones = data.get("Justificacion", [""] * len(data["EstudianteId"]))

        # Ahora iteramos sobre las 3 listas al mismo tiempo usando zip()
        assitances = [Asistencia({
            "EstudianteId": e,
            "ClaseId": data["ClaseId"],
            "Activo": a,
            "Justificacion": j
        }) for e, a, j in zip(data["EstudianteId"], data["Activo"], justificaciones)]
        # -----------------------------------------

        count = rep.create(assitances)

        if count == 0:
            raise ValidationError(f"No se pudieron crear las asistencias")

        classroom = ClaseRep().get(data["ClaseId"])

        AuditoriaRep().create(Auditoria({
            "Accion": "Registro",
            "Descripcion": f"Asistencias registradas {classroom.curso.grado}° año, sección \"{number_to_letter(classroom.seccion)}\"",
            "Usuario": Usuario({"id": payload["id"]})
        }))

        return Response(status=201)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]