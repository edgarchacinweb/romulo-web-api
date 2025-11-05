from enum import Enum
from models.Horario import Horario
from models.Docente import Docente
from models.BloqueHorario import BloqueHorario

class Dia(Enum):
    MONDAY = "Lunes"
    TUESDAY = "Martes"
    WEDNESDAY = "Miércoles"
    THURSDAY = "Jueves"
    FRIDAY = "Viernes"

class HorarioItem():
    def __init__(self, *args):
        self.id: str = None
        self.Dia: Dia = None
        self.bloque_horario: BloqueHorario = None
        self.Docente: Docente = None
        self.Horario: Horario = None
        self.Actividad: str = None

        if len(args) > 1:
            self.id = args[0]
            if isinstance(args[1], Dia):
                self.Dia = args[1]
            else:
                self.Dia = getattr(Dia, args[1])
            self.HoraInicio = args[2]
            self.Docente = args[3]
            self.Horario = args[4]
            if len(args) > 4: self.Actividad = args[5]
        elif len(args) == 1 and isinstance(args[0], dict):
            schedule = args[0]
            if "id" in schedule: self.id = schedule["id"]
            if "Dia" in schedule:
                if isinstance(schedule["Dia"], Dia):
                    self.Dia = schedule["Dia"]
                elif isinstance(schedule["Dia"], str) and hasattr(Dia, schedule["Dia"]):
                    self.Dia = getattr(Dia, schedule["Dia"])
                else:
                    self.Dia = Dia(schedule["Dia"])
            if "BloqueHorario" in schedule: self.bloque_horario = schedule["BloqueHorario"]
            if "Docente" in schedule: self.Docente = schedule["Docente"]
            if "Horario" in schedule: self.Horario = schedule["Horario"]
            if "Actividad" in schedule: self.Actividad = schedule["Actividad"]
        else:
            schedule = args[0]
            if len(schedule) > 4:
                self.id = schedule[0]
                self.Dia = Dia(schedule[1])
                self.bloque_horario = schedule[2]
                self.Docente = schedule[3]
                self.Horario = schedule[4]
                if len(schedule) > 4: self.Actividad = schedule[4]

    def to_dict(self):
        schedule_dict = dict()
        if self.id: schedule_dict["HorarioId"] = self.id
        if self.Dia: schedule_dict["Dia"] = self.Dia.value
        if self.bloque_horario: schedule_dict["BloqueHorario"] = self.bloque_horario.to_dict()
        if self.Docente: schedule_dict["Docente"] = self.Docente.to_dict()
        if self.Horario: schedule_dict["Horario"] = self.Horario.to_dict()
        if self.Actividad: schedule_dict["Actividad"] = self.Actividad
            
        return schedule_dict

    def to_tuple(self):
        if self.Docente:
            return (self.bloque_horario.id, self.Dia.value, self.Docente.id, None, self.Horario.id)
        else:
            return (self.bloque_horario.id, self.Dia.value, None, self.Actividad, self.Horario.id)