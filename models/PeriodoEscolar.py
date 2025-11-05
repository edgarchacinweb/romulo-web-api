from datetime import date, datetime
from utils.helpers import str_to_date, date_to_str, str_to_datetime, datetime_to_str

class PeriodoEscolar():
    def __init__(self, *args):
        self.id: str = None
        self.fecha_inicio: date = None
        self.fecha_fin: date = None
        self.capacidad: int = None
        self.fecha_creacion: datetime = None
        
        if len(args) > 1:
            self.id = args[0]
            self.fecha_inicio = args[1]
            self.fecha_fin = args[2]
            self.capacidad = args[3]
            self.fecha_creacion = args[4]
        elif len(args) == 1 and isinstance(args[0], dict):
            sbj_dict = args[0]
            if "id" in sbj_dict: self.id = sbj_dict["id"]
            if "FechaInicio" in sbj_dict: self.fecha_inicio = str_to_date(sbj_dict["FechaInicio"])
            if "FechaFin" in sbj_dict: self.fecha_fin = str_to_date(sbj_dict["FechaFin"])
            if "Capacidad" in sbj_dict: self.capacidad = sbj_dict["Capacidad"]
            if "FechaCreacion" in sbj_dict: self.fecha_creacion = str_to_datetime(sbj_dict["FechaCreacion"])
        else:
            sbj_tuple = args[0]
            self.id = sbj_tuple[0]
            self.fecha_inicio = sbj_tuple[1]
            self.fecha_fin = sbj_tuple[2]
            self.capacidad = sbj_tuple[3]
            self.fecha_creacion = sbj_tuple[4]

    def to_dict(self):
        subject_dict = dict()
        if self.id: subject_dict["id"] = self.id
        if self.fecha_inicio: subject_dict["FechaInicio"] = date_to_str(self.fecha_inicio)
        if self.fecha_fin: subject_dict["FechaFin"] = date_to_str(self.fecha_fin)
        if self.capacidad: subject_dict["Capacidad"] = self.capacidad
        if self.fecha_creacion: subject_dict["FechaCreacion"] = datetime_to_str(self.fecha_creacion)
        return subject_dict
