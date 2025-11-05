from enum import Enum
from datetime import datetime
from models.PeriodoEscolar import PeriodoEscolar
from utils.helpers import str_to_datetime, datetime_to_str

class EstadoInscripcion(Enum):
    INSCRITO = 'inscrito'
    REINSCRITO = 'reinscrito'

class Inscripcion():

    def __init__(self, *args):
        self.id: str = None
        self.estudiante_id: str = None
        self.estado_inscripcion: EstadoInscripcion = None
        self.fecha_creacion: datetime = None
        
        if len(args) > 1:
            self.id = args[0]
            self.estudiante_id = args[1]
            self.estado_inscripcion = args[2]
            self.fecha_creacion = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            sbj_dict = args[0]
            if "id" in sbj_dict: self.id = sbj_dict["id"]
            if "EstudianteId" in sbj_dict: self.estudiante_id = sbj_dict["EstudianteId"]
            if "EstadoInscripcion" in sbj_dict:
                if isinstance(sbj_dict["EstadoInscripcion"], EstadoInscripcion):
                    self.estado_inscripcion = sbj_dict["EstadoInscripcion"]
                else:
                    self.estado_inscripcion = EstadoInscripcion(sbj_dict["EstadoInscripcion"])
            if "FechaCreacion" in sbj_dict: self.fecha_creacion = str_to_datetime(sbj_dict["FechaCreacion"])
        else:
            sbj_tuple = args[0]
            self.id = sbj_tuple[0]
            self.estudiante_id = sbj_tuple[1]
            self.estado_inscripcion = sbj_tuple[2]
            self.fecha_creacion = sbj_tuple[3]

    def to_dict(self):
        subject_dict = dict()
        if self.id: subject_dict["InscripcionId"] = self.id
        if self.estudiante_id: subject_dict["EstudianteId"] = self.estudiante_id
        if self.estado_inscripcion: subject_dict["EstadoInscripcion"] = self.estado_inscripcion.value
        if self.fecha_creacion: subject_dict["FechaCreacion"] = datetime_to_str(self.fecha_creacion)
        return subject_dict
    
    def to_tuple(self):
        return (self.estudiante_id, self.estado_inscripcion)
