from utils.exceptions import *
from utils.logger import Logger
from typing import Tuple, Dict
import traceback
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from psycopg2.errors import UniqueViolation, RaiseException

def exception_handler(exception: Exception) -> Tuple[Dict[str,str], int]:
    Logger().error(traceback.format_exc())
    msg: Dict[str, str] = {"message": exception.__str__()}

    if isinstance(exception, (MissingEntityData, ValidationError, InvalidFileType, UploadFileError, InvalidId, InvalidFileType, EmailException, ValueError)):
        code = 400
    elif isinstance(exception, UniqueViolation):
        code = 400
        duplicated = exception.pgerror.split("(\"")[1].split("\")")[0].lower()

        if duplicated == "cedula":
            duplicated = "cédula de identidad"
        elif duplicated == "email":
            duplicated = "correo electrónico"
        elif duplicated == "telefono":
            duplicated = "teléfono"

        msg = {"message": f"Campo {duplicated} duplicado"}
    elif isinstance(exception, RaiseException):
        code = 500
        msg = {"message": exception.diag.message_primary}
    elif isinstance(exception, EntityAlreadyExists):
        code = 409
    elif isinstance(exception, (Unauthorized, InvalidOtpCode)):
        code = 401
    elif isinstance(exception, UnsupportedMediaType):
        msg = {"message": "La cabecera Content-Type no es compatible con valores de tipo JSON"}
        code = 415
    elif isinstance(exception, BadRequest) and "Failed to decode JSON object" in exception.__str__():
        msg = {"message": "Hubo un error al decodificar el JSON. No se han envíados datos o tiene un formato inválido"} 
        code = 400
    elif isinstance(exception, (EntityUpdateError, InsertEntityError, EntityDeleteError)):
        code = 500
    elif isinstance(exception, EntityNotFound):
        code = 404
    else:
        msg = {"message": "Ocurrió un error en el servidor"}
        code = 500
    
    return msg, code
