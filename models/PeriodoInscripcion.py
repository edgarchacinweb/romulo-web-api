from models.PeriodoEscolar import PeriodoEscolar
from datetime import date
from utils.helpers import str_to_date, date_to_str

class PeriodoInscripcion:

    def __init__(self, *args):
        self.id: str = None
        self.start: date = None
        self.end: date = None
        self.periodo_escolar: PeriodoEscolar = None
        
        if len(args) > 1:
            self.id = args[0]
            self.start = str_to_date(args[1])
            self.end = str_to_date(args[2])
            self.periodo_escolar = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            dp_dict = args[0]
            if "id" in dp_dict: self.id = dp_dict["id"]
            if "Inicio" in dp_dict: self.start = str_to_date(dp_dict["Inicio"])
            if "Fin" in dp_dict: self.end = str_to_date(dp_dict["Fin"])
            if "PeriodoEscolar" in dp_dict: self.periodo_escolar = dp_dict["PeriodoEscolar"]
        else:
            dp_tuple = args[0]
            self.id = dp_tuple[0]
            self.start = str_to_date(dp_tuple[1])
            self.end = str_to_date(dp_tuple[2])
            self.periodo_escolar = dp_tuple[3]

    def to_dict(self):
        reg_dict = dict()
        reg_dict["InscripcionId"] = self.id
        if self.start: reg_dict["Inicio"] = self.start.strftime("%Y-%m-%d")
        if self.end: reg_dict["Fin"] = self.end.strftime("%Y-%m-%d")
        if self.periodo_escolar: reg_dict["PeriodoEscolar"] = self.periodo_escolar.to_dict()
        return reg_dict
    
    def to_tuple(self):
        return (date_to_str(self.start), date_to_str(self.end), self.periodo_escolar.id)