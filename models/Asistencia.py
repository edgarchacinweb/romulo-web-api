from models.Estudiante import Estudiante
from models.Clase import Clase

class Asistencia():

    def __init__(self, *args):
        self.id: str = None
        self.clase: Clase = None
        self.estudiante: Estudiante = None
        self.activo: bool = False
        
        if len(args) > 1:
            self.id = args[0]
            self.clase = args[1]
            self.estudiante = args[2]
            self.activo = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            sbj_dict = args[0]
            if "id" in sbj_dict: self.id = sbj_dict["id"]
            if "ClaseId" in sbj_dict: self.clase = Clase({"id": sbj_dict["ClaseId"]})
            if "Clase" in sbj_dict: self.clase = sbj_dict["Clase"]
            if "EstudianteId" in sbj_dict: self.estudiante = Estudiante({"id": sbj_dict["EstudianteId"]})
            if "Estudiante" in sbj_dict: self.estudiante = sbj_dict["Estudiante"]
            if "Activo" in sbj_dict: self.activo = sbj_dict["Activo"]
        else:
            sbj_tuple = args[0]
            self.id = sbj_tuple[0]
            self.clase = sbj_tuple[1]
            self.estudiante = sbj_tuple[2]
            self.activo = sbj_tuple[3]

    def to_dict(self):
        subject_dict = dict()
        if self.id: subject_dict["AsistenciaId"] = self.id
        if self.clase: subject_dict["Clase"] = self.clase.to_dict()
        if self.estudiante: subject_dict["Estudiante"] = self.estudiante.to_dict()
        subject_dict["Activo"] = self.activo
        return subject_dict

    def to_tuple(self):
        return (self.estudiante.id, self.clase.id, self.activo)
