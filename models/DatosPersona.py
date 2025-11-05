from utils.logger import Logger
from utils.validations import Validations
from utils.exceptions import InvalidId, ValidationError
from utils.helpers import capitalize

class DatosPersona:

    def __init__(self, *args):
        self.id = None
        self.first_name: str = None
        self.last_name: str = None
        self.gender = None
        self.ci = None
        self.phone = None
        self.direccion = None
        self.ocupacion = None
        
        if len(args) > 1:
            Logger().debug(args)
            self.id = args[0]
            self.first_name = args[1]
            self.last_name = args[2]
            self.gender = args[3]
            self.ci = args[4]
            self.phone = args[5]
            self.direccion = args[6]
            self.ocupacion = args[7]
        elif len(args) == 1 and isinstance(args[0], dict):
            dp_dict = args[0]
            if "id" in dp_dict: self.id = dp_dict["id"]
            if "Nombre" in dp_dict: self.first_name = dp_dict["Nombre"]
            if "Apellido" in dp_dict: self.last_name = dp_dict["Apellido"]
            if "Sexo" in dp_dict: self.gender = dp_dict["Sexo"]
            if "Cedula" in dp_dict: self.ci = dp_dict["Cedula"]
            if "Telefono" in dp_dict: self.phone = dp_dict["Telefono"]
            if "Direccion" in dp_dict: self.direccion = dp_dict["Direccion"]
            if "Ocupacion" in dp_dict: self.ocupacion = dp_dict["Ocupacion"]
        else:
            dp_tuple = args[0]
            self.id = dp_tuple[0]
            self.first_name = dp_tuple[1]
            self.last_name = dp_tuple[2]
            self.gender = dp_tuple[3]
            self.ci = dp_tuple[4]
            self.phone = dp_tuple[5]
            self.direccion = dp_tuple[6]
            self.ocupacion = dp_tuple[7]

        self._validate()

    def to_dict(self):
        dp = dict()
        if self.id: dp["DatosPersonaId"] = self.id
        if self.first_name: dp["Nombre"] = self.first_name
        if self.last_name: dp["Apellido"] = self.last_name
        if self.gender: dp["Sexo"] = self.gender
        if self.ci: dp["Cedula"] = self.ci
        if self.phone: dp["Telefono"] = self.phone
        if self.direccion: dp["Direccion"] = self.direccion
        if self.ocupacion: dp["Ocupacion"] = self.ocupacion
        return dp
    
    def _validate(self):
        if self.first_name and self.last_name:
            self.first_name = capitalize(self.first_name)
            self.last_name = capitalize(self.last_name)

        # if self.ci and not Validations.is_ci(f"{self.ci}"):
        #     raise ValidationError("La cédula de identidad introducida tiene un formato inválido")
        elif self.phone and not Validations.is_phone(self.phone):
            raise ValidationError("El número de teléfono introducido tiene un formato inválido")
        elif self.gender and not Validations.is_gender(self.gender):
            raise ValidationError("Sólo puedes introducir cómo genero \"Masculino\" o \"Femenino\"")
        elif self.id and not Validations.is_uuid(self.id):
            raise InvalidId("El ID es inválido")
        elif self.first_name and not Validations.is_name(self.first_name):
            raise ValidationError("El nombre tiene un formato inválido")
        # elif self.last_name and not Validations.is_lastname(self.last_name):
        #     raise ValidationError("El apellido tiene un formato inválido")
