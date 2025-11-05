from datetime import date, time
from utils.helpers import str_to_date, date_to_str, str_to_time, time_to_str

class BloqueHorario():
    def __init__(self, *args):
        self.id: str = None
        self.hora_inicio: time = None
        self.hora_fin: time = None
        self.activo: bool = False
        self.fecha: date = None

        if len(args) > 1:
            self.id = args[0]
            self.hora_inicio = str_to_time(args[1])
            self.hora_fin = str_to_time(args[2])
            self.activo = args[3]
            self.fecha = str_to_date(args[4])
        elif len(args) == 1 and isinstance(args[0], dict):
            block_dict = args[0]
            if "id" in block_dict: self.id = block_dict["id"]
            if "HoraInicio" in block_dict: self.hora_inicio = str_to_time(block_dict["HoraInicio"])
            if "HoraFin" in block_dict: self.hora_fin = str_to_time(block_dict["HoraFin"])
            if "Activo" in block_dict: self.activo = block_dict["Activo"]
            if "Fecha" in block_dict: self.fecha = str_to_date(block_dict["Fecha"])
        else:
            block_tuple = args[0]
            self.id = block_tuple[0]
            self.hora_inicio = str_to_time(block_tuple[1])
            self.hora_fin = str_to_time(block_tuple[2])
            self.activo = block_tuple[3]
            self.fecha = str_to_date(block_tuple[4])

    def to_dict(self):
        model_dict = dict()
        if self.id: model_dict["BloqueHorarioId"] = self.id
        if self.hora_inicio: model_dict["HoraInicio"] = self.hora_inicio.strftime("%H:%M %p")
        if self.hora_fin: model_dict["HoraFin"] = self.hora_fin.strftime("%H:%M %p")
        if self.activo: model_dict["Activo"] = self.activo
        if self.fecha: model_dict["Fecha"] = date_to_str(self.fecha)
        return model_dict
    
    def to_tuple(self):
        return (self.hora_inicio, self.hora_fin)
