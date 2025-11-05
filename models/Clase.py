from models.Docente import Docente
from models.PeriodoEscolar import PeriodoEscolar
from models.Curso import Curso
from datetime import date
from utils.helpers import str_to_date, date_to_str

class Clase():

    def __init__(self, *args):
        self.id: str = None
        self.docente: Docente = None
        self.curso: Curso = None
        self.periodo_escolar: PeriodoEscolar = None
        self.seccion: int = None
        self.fecha: date = None
        
        if len(args) > 1:
            self.id = args[0]
            self.docente = args[1]
            self.periodo_escolar = args[2]
            self.curso = args[3]
            self.seccion = args[4]
            self.fecha = args[5]
        elif len(args) == 1 and isinstance(args[0], dict):
            sbj_dict = args[0]
            if "id" in sbj_dict: self.id = sbj_dict["id"]
            if "Docente" in sbj_dict: self.docente = sbj_dict["Docente"]
            if "PeriodoEscolar" in sbj_dict: self.periodo_escolar = sbj_dict["PeriodoEscolar"]
            if "Curso" in sbj_dict: self.curso = sbj_dict["Curso"]
            if "Seccion" in sbj_dict: self.seccion = sbj_dict["Seccion"]
            if "Fecha" in sbj_dict: self.fecha = str_to_date(sbj_dict["Fecha"])
        else:
            sbj_tuple = args[0]
            self.id = sbj_tuple[0]
            self.docente = sbj_tuple[1]
            self.periodo_escolar = sbj_tuple[2]
            self.curso = sbj_tuple[3]
            self.seccion = sbj_tuple[4]
            self.fecha = sbj_tuple[5]

    def to_dict(self):
        subject_dict = dict()
        if self.id: subject_dict["ClaseId"] = self.id
        if self.docente: subject_dict["Docente"] = self.docente.to_dict()
        if self.periodo_escolar: subject_dict["PeriodoEscolar"] = self.periodo_escolar.to_dict()
        if self.curso: subject_dict["Curso"] = self.curso.to_dict()
        if self.seccion: subject_dict["Seccion"] = self.seccion
        if self.fecha: subject_dict["FechaCreacion"] = date_to_str(self.fecha)
        return subject_dict
    
    def to_tuple(self):
        return (self.docente.id, self.curso.id, self.periodo_escolar.id, self.seccion)
