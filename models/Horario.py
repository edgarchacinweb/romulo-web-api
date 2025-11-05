from models.Curso import Curso
from models.PeriodoEscolar import PeriodoEscolar

class Horario():
    def __init__(self, *args):
        self.id: str = None
        self.curso: Curso = None
        self.periodo_escolar: PeriodoEscolar = None
        self.seccion: int = None

        if len(args) > 1:
            self.id = args[0]
            self.curso = args[1]
            self.periodo_escolar = args[2]
            self.seccion = args[3]
        elif len(args) == 1 and isinstance(args[0], dict):
            schedule = args[0]
            if "id" in schedule: self.id = schedule["id"]
            if "Curso" in schedule: self.curso = schedule["Curso"]
            if "PeriodoEscolar" in schedule: self.periodo_escolar = schedule["PeriodoEscolar"]
            if "Seccion" in schedule: self.seccion = schedule["Seccion"]
        else:
            schedule = args[0]
            self.id = schedule[0]
            self.curso = schedule[1]
            self.periodo_escolar = schedule[2]
            self.seccion = schedule[3]

    def to_dict(self):
        schedule_dict = dict()
        if self.id: schedule_dict["HorarioId"] = self.id
        if self.curso: schedule_dict["Curso"] = self.curso.to_dict()
        if self.periodo_escolar: schedule_dict["PeriodoEscolar"] = self.periodo_escolar.to_dict()
        if self.seccion: schedule_dict["Seccion"] = self.seccion
        return schedule_dict

    def to_tuple(self):
        return (self.curso.id, self.seccion)
