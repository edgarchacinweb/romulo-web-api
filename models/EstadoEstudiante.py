from enum import Enum
from datetime import datetime
from utils.helpers import str_to_datetime, datetime_to_str

class Estado_Estudiante(Enum):
    REVIEW = 'revision'
    REGISTERED ='inscrito'
    RETIRED ='retirado'
    GRADUATED = 'graduado'

class EstadoEstudiante():
    def __init__(self, *args):
        self.id: str = None
        self.estudiante_id: str = None
        self.estado: Estado_Estudiante = None
        self.fecha_creacion: datetime = None

        if len(args) > 1:
            self.id = args[0]
            self.estudiante_id = args[1]
            self.estado = args[2]
            self.fecha_creacion = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            state_dict = args[0]
            if "id" in state_dict: self.id = state_dict["id"]
            if "EstudianteId" in state_dict: self.estudiante_id = state_dict["EstudianteId"]
            if "Estado" in state_dict: self.estado = state_dict["Estado"]
            if "FechaCreacion" in state_dict: self.fecha_creacion = str_to_datetime(state_dict["FechaCreacion"])
        else:
            state_tuple = args[0]
            self.id = state_tuple[0]
            self.estudiante_id = state_tuple[1]
            self.estado = state_tuple[2]
            self.fecha_creacion = state_tuple[3]

    def to_dict(self):
        e_dict = dict()
        e_dict["EstadoEstudianteId"] = self.id
        e_dict["EstudianteId"] = self.estudiante_id
        e_dict["Estado"] = self.estado
        e_dict["FechaCreacion"] = datetime_to_str(self.fecha_creacion)
        return e_dict

    def to_tuple(self):
        return (self.estudiante_id, self.estado)
