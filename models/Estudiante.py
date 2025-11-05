from datetime import date
from models.Curso import Curso
from models.DatosPersona import DatosPersona
from utils import helpers

class Estudiante():

    def __init__(self, *args):
        self.id: str = None
        self.birthdate: date = None
        self.datos_persona: DatosPersona = DatosPersona({})
        self.representante: DatosPersona = DatosPersona({})
        
        if len(args) > 1:
            self.id = args[0]
            self.birthdate = helpers.str_to_date(args[1])
            self.datos_persona.id = args[2]
            self.representante.id = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            student_dict = args[0]
            if "id" in student_dict: self.id = student_dict["id"]
            if "FechaNacimiento" in student_dict: self.birthdate = helpers.str_to_date(student_dict["FechaNacimiento"])
            if "DatosPersona" in student_dict: self.datos_persona = student_dict["DatosPersona"]
            if "DatosPersonaId" in student_dict: self.datos_persona.id = student_dict["DatosPersonaId"]
            if "RepresentanteId" in student_dict: self.representante.id = student_dict["RepresentanteId"]
            if "Representante" in student_dict: self.representante = student_dict["Representante"]
        else:
            student_tuple = args[0]
            self.id = student_tuple[0]
            self.birthdate = helpers.str_to_date(student_tuple[1])
            self.datos_persona.id = student_tuple[2]
            self.representante.id = student_tuple[3]

    def to_dict(self):
        student = dict()
        if self.id: student["EstudianteId"] = self.id
        if self.datos_persona: student["DatosPersona"] = self.datos_persona.to_dict()
        if self.representante: student["Representante"] = self.representante.to_dict()
        if self.birthdate: student["FechaNacimiento"] = helpers.date_to_str(self.birthdate)
        return student

    def to_tuple(self):
        return (
            helpers.date_to_str(self.birthdate),
            self.datos_persona.id,
            self.representante.id
        )
