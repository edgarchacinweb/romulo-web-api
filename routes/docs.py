from flask import Blueprint, jsonify, request, Response, send_file
from utils.logger import Logger
from database.Estudiante import EstudianteRep
from database.DatosPersona import DatosPersonaRep
from utils.exceptions import *
from utils.handler import exception_handler
from utils.validations import Validations
from utils.image import resize, get_format
from PIL import Image
from utils.config import app
from pathlib import Path
from utils.Security import Security
from models.Usuario import Rol
from models.DatosPersona import DatosPersona
from database.DatosPersona import DatosPersonaRep

logger = Logger()
docs_bp = Blueprint("docs", __name__)

@docs_bp.route("/docs/create", methods=["POST"])
def create_docs():
    try:
        student_id = request.form.get("EstudianteId") or ""
        parent_id = request.form.get("RepresentanteId") or ""
        files = request.files

        logger.debug(files, "FILES")

        # Validing files and IDs
        if any(file not in files for file in ("FotoEstudiante", "FotoRepresentante", "DocumentoEstudiante", "DocumentoRepresentante")):
            raise MissingEntityData("Faltan archivos para completar el registro")
        elif not Validations.is_uuid(student_id):
            raise InvalidId("El ID del estudiante es inválido")
        elif not Validations.is_uuid(parent_id):
            raise InvalidId("El ID del representante es inválido")
        elif not Validations.valid_format(files["FotoEstudiante"].filename):
            raise InvalidFileType("Foto del estudiante inválida: solo se permiten los formatos png, jpeg, jpg y webp")
        elif not Validations.valid_format(files["FotoRepresentante"].filename):
            raise InvalidFileType("Foto del representante inválida: solo se permiten los formatos png, jpeg, jpg y webp")
        elif not Validations.is_pdf(files["DocumentoRepresentante"]):
            raise InvalidFileType("Documento del representante inválido: solo se permiten archivos PDF")
        elif not Validations.is_pdf(files["DocumentoEstudiante"]):
            raise InvalidFileType("Documento del estudiante inválido: solo se permiten archivos PDF")
        elif files["DocumentoRepresentante"].content_length / 1024 > app.config["MAX_PDF_SIZE"]:
            raise UploadFileError(f"El documento del representante es demasiado grande. Tamaño máximo: {app.config['MAX_PDF_SIZE'] * 1024} MB")
        elif files["DocumentoEstudiante"].content_length / 1024 > app.config["MAX_PDF_SIZE"]:
            raise UploadFileError(f"El documento del estudiante es demasiado grande. Tamaño máximo: {app.config['MAX_PDF_SIZE'] * 1024} MB")

        # Check if exists student
        student = EstudianteRep().get(student_id)

        if not student:
            raise EntityNotFound(f"El estudiante no está registrado en la base de datos ")
        
        # Check if exists parent
        parent = DatosPersonaRep().get(parent_id)

        if not parent:
            raise EntityNotFound(f"El representante no está registrado en la base de datos ")
        
        # Check if exists docs
        upload_folder: str = app.config["UPLOAD_FOLDER"] + "/"
        student_photo = Path(upload_folder + student_id + ".webp")
        parent_photo = Path(upload_folder + parent_id + ".webp")
        student_doc = Path(upload_folder + student_id + ".pdf")
        parent_doc = Path(upload_folder + parent_id + ".pdf")

        if student_photo.exists():
            student_photo.unlink()
        if parent_photo.exists():
            parent_photo.unlink()
        if student_doc.exists():
            student_doc.unlink()
        if parent_doc.exists():
            parent_doc.unlink()

        # proccessing images
        photo1: Image = resize(files["FotoEstudiante"])
        photo2: Image = resize(files["FotoRepresentante"])
        
        photo1.save(upload_folder + student_id + ".webp", "webp")
        photo2.save(upload_folder + parent_id + ".webp", "webp")

        # proccessing pdf
        pdf_parent = files["DocumentoRepresentante"]
        pdf_student = files["DocumentoEstudiante"]
        pdf_parent.save(upload_folder + parent_id + ".pdf")
        pdf_student.save(upload_folder + student_id + ".pdf")

        return Response(status=201)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@docs_bp.route("/docs/create/<string:ci>", methods=["POST"])
def create_doc(ci: str):
    try:
        payload = Security.verify_token(request.headers)
        files = request.files
        photo_name: str = files["Foto"].filename

        if not payload or payload["role"] != Rol.ADMIN.name:
            raise Unauthorized()
        elif not Validations.is_ci(ci):
            raise InvalidId("La cédula de identidad tiene un formato inválido")
        elif not Validations.valid_format(photo_name):
            raise InvalidFileType("Foto inválida: solo se permiten los formatos png, jpeg, jpg y webp")
        elif not Validations.is_pdf(files["Documento"]):
            raise InvalidFileType("Documento inválido: solo se permiten archivos PDF")
        elif files["Documento"].content_length / 1024 > app.config["MAX_PDF_SIZE"]:
            raise UploadFileError(f"El documento es demasiado grande. Tamaño máximo: {app.config['MAX_PDF_SIZE'] * 1024} MB")
        
        rep = DatosPersonaRep()
        logger.debug(ci, "CEDULA DE IDENTIDAD")
        person: DatosPersona = rep.get_by_ci(int(ci));
        upload_folder: str = app.config["UPLOAD_FOLDER"] + "/"
        photo_path = Path(upload_folder + person.id + ".webp")
        document_path = Path(upload_folder + person.id + ".pdf")

        if photo_path.exists():
            photo_path.unlink()
        if document_path.exists():
            document_path.unlink()

        photo: Image = resize(files["Foto"])
        pdf = files["Documento"]

        photo.save(photo_path)
        pdf.save(document_path)
        
        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

@docs_bp.route("/docs/get/<string:resource>", methods=["GET"])
def get_docs(resource: str = ""):
    try:
        upload_folder: str = app.config["UPLOAD_FOLDER"]
        url = f"{upload_folder}/{resource}"

        resource_url: Path = Path(url)
        img_format = get_format(resource)

        if not resource_url.exists():
            raise EntityNotFound("No se encontró ninguna imagen o documento asociada al ID")

        return send_file(resource_url, mimetype="image/webp" if img_format == "webp" else "application/pdf")
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
