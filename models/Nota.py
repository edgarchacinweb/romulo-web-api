from models.Materia import Materia
from models.Boleta import Boleta
from utils.logger import Logger

class Nota():
    def __init__(self, *args):
        self.id: str = None
        self.ponderacion: int = None
        self.lapso: int = None
        self.materia: Materia = None
        self.boleta: Boleta = None

        if len(args) > 1:
            self.id = args[0]
            self.ponderacion = args[1]
            self.lapso = args[2]
            self.materia = args[3]
            self.boleta = args[4]
        elif len(args) == 1 and isinstance(args[0], dict):
            calification_dict = args[0]
            if "NotaId" in calification_dict: self.id = calification_dict["NotaId"]
            if "Ponderacion" in calification_dict: self.ponderacion = calification_dict["Ponderacion"]
            if "Lapso" in calification_dict: self.lapso = calification_dict["Lapso"]
            if "Materia" in calification_dict: self.materia = calification_dict["Materia"]
            if "Boleta" in calification_dict: self.boleta = calification_dict["Boleta"]
        else:
            calification_tuple = args[0]
            self.id = calification_tuple[0]
            self.ponderacion = calification_tuple[1]
            self.lapso = calification_tuple[2]
            self.materia = calification_tuple[3]
            self.boleta = calification_tuple[4]

    def to_dict(self):
        schedule_dict = dict()
        Logger().debug(self.boleta, "BOLETA")
        if self.id: schedule_dict["NotaId"] = self.id
        if self.ponderacion: schedule_dict["Ponderacion"] = self.ponderacion
        if self.lapso: schedule_dict["Lapso"] = self.lapso
        if self.materia: schedule_dict["Materia"] = self.materia.to_dict()
        if self.boleta: schedule_dict["Boleta"] = self.boleta.to_dict()
            
        return schedule_dict

    def to_tuple(self):
        return (self.ponderacion, self.lapso, self.materia.id, self.boleta.id)
