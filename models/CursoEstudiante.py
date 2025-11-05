from models.PeriodoEscolar import PeriodoEscolar
from models.Estudiante import Estudiante
from models.Curso import Curso
from datetime import datetime
from utils.helpers import str_to_datetime, datetime_to_str

class CursoEstudiante():

    def __init__(self, *args):
        self.id: str = None
        self.estudiante: Estudiante
        self.curso: Curso = None
        self.seccion: int = None
        self.periodo_escolar: PeriodoEscolar = None
        self.fecha_creacion: datetime = None
        
        if len(args) > 1:
            self.id = args[0]
            self.estudiante = args[1]
            self.curso = args[2]
            self.seccion = args[3]
            self.fecha_creacion = args[4]
        elif len(args) == 1 and isinstance(args[0], dict):
            course_dict = args[0]
            if "id" in course_dict: self.id = course_dict["id"]
            if "EstudianteId" in course_dict: self.estudiante = Estudiante({"id": course_dict["EstudianteId"]})
            if "Estudiante" in course_dict: self.estudiante = course_dict["Estudiante"]
            if "CursoId" in course_dict: self.curso = Curso({"id": course_dict["CursoId"]})
            if "Curso" in course_dict: self.curso = course_dict["Curso"]
            if "Seccion" in course_dict: self.seccion = course_dict["Seccion"]
            if "PeriodoEscolar" in course_dict: self.periodo_escolar = course_dict["PeriodoEscolar"]
            if "FechaCreacion" in course_dict: self.fecha_creacion = str_to_datetime(course_dict["FechaCreacion"])
        else:
            course_tuple = args[0]
            self.id = course_tuple[0]
            self.estudiante_id = course_tuple[1]
            self.curso_id = course_tuple[2]
            self.seccion = course_tuple[3]
            self.fecha_creacion = course_tuple[4]

    def to_dict(self):
        course = dict()
        if self.id: course["CursoId"] = self.id
        if self.estudiante: course["Estudiante"] = self.estudiante.to_dict()
        if self.curso: course["Curso"] = self.curso.to_dict()
        if self.seccion: course["Seccion"] = self.seccion
        if self.fecha_creacion: course["FechaCreacion"] = datetime_to_str(self.fecha_creacion)
        if self.periodo_escolar: course["PeriodoEscolar"] = self.periodo_escolar
        return course

    def to_tuple(self):
        return (self.estudiante.id, self.curso.id, self.periodo_escolar.id)
