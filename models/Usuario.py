from enum import Enum
from models.DatosPersona import DatosPersona
from utils.validations import Validations
from utils.exceptions import InvalidId, ValidationError
from utils.logger import Logger
from utils.helpers import str_to_date, date_to_str
from datetime import date

class Rol(Enum):
    ADMIN = "administrador"
    TEACHER = "docente"
    PARENT = "representante"

class Usuario():
    def __init__(self, *args):
        self.id: str = None
        self.email: str = None
        self.password: str = None
        self.role: Rol = None
        self.fecha_creacion: date = None
        self.DatosPersonaId: str = None
        self.DatosPersona: DatosPersona = None

        if len(args) > 1:
            self.id = args[0]
            self.email = args[1]
            self.password = args[2]
            self.role = getattr(Rol, args[3])
            self.DatosPersonaId = args[4]
            self.DatosPersona = DatosPersona(args[5], args[6], args[7], args[8], args[9], args[10])
        elif len(args) == 1 and isinstance(args[0], dict):
            user = args[0]
            if "id" in user: self.id = user["id"]
            if "Email" in user: self.email = user["Email"]
            if "Clave" in user: self.password = user["Clave"]
            if "Rol" in user:
                Logger().debug(type(user["Rol"]), "Usuario model, Rol")
                if isinstance(user["Rol"], Rol):
                    self.role = user["Rol"]
                else:
                    self.role = getattr(Rol, user["Rol"])
            if "FechaCreacion" in user: self.fecha_creacion = str_to_date(user["FechaCreacion"])
            if "DatosPersonaId" in user: self.DatosPersonaId = user["DatosPersonaId"]
            if "DatosPersona" in user: self.DatosPersona = user["DatosPersona"]
        else:
            user = args[0]
            if len(user) > 4:
                self.id = user[0]
                self.email = user[1]
                self.password = user[2]
                self.role = Rol(user[3])
                self.DatosPersonaId = user[4]
                if len(user) == 11:
                    self.DatosPersona = DatosPersona(user[5], user[6], user[7], user[8], user[9], user[10])
                elif len(user) >= 15:
                    self.DatosPersona = DatosPersona(user[7], user[8], user[9], user[10], user[11], user[12], user[13], user[14])

        self._validate()

    def to_dict(self):
        user = dict()
        if self.id: user["UsuarioId"] = self.id
        if self.email: user["Email"] = self.email
        # if self.password: user["Clave"] = self.password
        if self.role: user["Rol"] = self.role.value
        if self.fecha_creacion: user["FechaCreacion"] = date_to_str(self.fecha_creacion)
        if self.DatosPersonaId: user["DatosPersonaId"] = self.DatosPersonaId
        if self.DatosPersona: user["DatosPersona"] = self.DatosPersona.to_dict()
        return user

    def _validate(self):
        if self.email and not Validations.is_email(self.email):
            raise ValidationError("El correo electrónico tiene un formato inválido")
        elif self.DatosPersonaId and not Validations.is_uuid(self.DatosPersonaId):
            raise InvalidId("El ID es inválido")