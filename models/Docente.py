from models.DatosPersona import DatosPersona
from models.Materia import Materia
from typing import List

class Docente():

    def __init__(self, *args):
        self.id: str = None
        self.datos_persona: DatosPersona = None
        self.fecha_creacion: Date = None
        self.materia: Materia = None
        self.materias: List[Materia] = None
        
        if len(args) > 1:
            self.id = args[0]
            self.datos_persona = args[1]
            self.materia = args[2]
            self.materias = args[3]
            self.fecha_creacion = args[4]
        elif len(args) == 1 and isinstance(args[0], dict):
            dcn_dict = args[0]
            if "id" in dcn_dict: self.id = dcn_dict["id"]
            if "DatosPersona" in dcn_dict: self.datos_persona = dcn_dict["DatosPersona"]
            if "Materia" in dcn_dict: self.materia = dcn_dict["Materia"]
            if "Materias" in dcn_dict: self.materias = dcn_dict["Materias"]
            if "FechaCreacion" in dcn_dict: self.fecha_creacion = dcn_dict["FechaCreacion"]
        else:
            dcn_tuple = args[0]
            self.id = dcn_tuple[0]
            self.datos_persona = dcn_tuple[1]
            self.materia = dcn_tuple[2]
            self.materias = dcn_tuple[3]
            self.fecha_creacion = dcn_tuple[4]

    def to_dict(self):
        dcn_dict = dict()
        if self.id: dcn_dict["DocenteId"] = self.id
        if self.datos_persona: dcn_dict["DatosPersona"] = self.datos_persona.to_dict()
        if self.materia: dcn_dict["Materia"] = self.materia.to_dict()
        if self.materias: dcn_dict["Materias"] = self.materias
        if self.fecha_creacion: dcn_dict["FechaCreacion"] = self.fecha_creacion
        return dcn_dict

    def to_tuple(self):
        return (self.datos_persona.id, self.materia.id)
