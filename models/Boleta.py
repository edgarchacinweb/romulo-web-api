from models.Estudiante import Estudiante
from models.PeriodoEscolar import PeriodoEscolar

class Boleta():
    def __init__(self, *args):
        self.id = None
        self.estudiante = None
        self.periodo_escolar = None

        if len(args) > 1:
            self.id = args[0]
            self.estudiante = args[1]
            self.periodo_escolar = args[2]
        elif len(args) == 1 and isinstance(args[0], dict):
            b_dict = args[0]
            if "id" in b_dict: self.id = b_dict["id"]
            if "Estudiante" in b_dict: self.estudiante = b_dict["Estudiante"]
            if "PeriodoEscolar" in b_dict: self.periodo_escolar = b_dict["PeriodoEscolar"]
        elif len(args) == 1 and isinstance(args[0], tuple):
            b = args[0]
            if len(b) > 0:
                self.id = b[0]
                self.estudiante = b[1]
                self.periodo_escolar = b[2]

    def to_dict(self):
        report = dict()
        if self.id: report["BoletaId"] = self.id
        if self.estudiante: report["Estudiante"] = self.estudiante.to_dict()
        if self.curso: report["PeriodoEscolar"] = self.periodo_escolar.to_dict()

        return report

    def to_tuple(self): 
        return (self.estudiante.id, self.curso.id, self.periodo_escolar.id)
