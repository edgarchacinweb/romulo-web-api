from database.connection import Connection
from database.repository import Repository
from models.CursoEstudiante import CursoEstudiante
from models.Curso import Curso
from utils.logger import Logger
from models.Curso import Curso
from models.PeriodoEscolar import PeriodoEscolar
from utils.exceptions import *
from typing import List

class CursoRep(Repository):
    def __init__(self):
        self.logger = Logger()
        self.db_connection = Connection().get_connection()

    def create(self, model: Curso):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT \"CursoId\" FROM \"Curso\" WHERE \"Grado\"=%s AND \"Seccion\"=%s AND \"PeriodoEscolarId\"=%s;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.grado, model.seccion, model.periodo_escolar.id))
            id = cursor.fetchone()
            self.logger.debug(id, "Course created")
            if id:
                cursor.close()
                raise EntityAlreadyExists(f"El curso académico ya se encuentra registrado")

            sql = "SELECT * FROM crear_curso(%s,%s,%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
            id = cursor.fetchone()[0]
            cursor.close()

            if not id:
                raise InsertEntityError(f"No se pudo insertar el siguiente registro: {model.to_dict()}")

            self.db_connection.commit()
            return id
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Curso\" ORDER BY \"Grado\" ASC;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            courses = cursor.fetchall()
            cursor.close()

            return [Curso({
                "id": c[0],
                "Grado": c[1]
            }) for c in courses]
        except Exception as err:
            self.db_connection.rollback()
            raise err
    
    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_curso(%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        course = cursor.fetchone()
        cursor.close()

        if not course or len(course) < 1:
            raise EntityNotFound(f"No se encontró ningún horario con ese identificador")

        return Curso({
            "id": course[0],
            "Grado": course[1],
            "Seccion": course[2],
            "Capacidad": course[3],
            "PeriodoEscolar": PeriodoEscolar({
                "id": course[4],
                "FechaInicio": course[5],
                "FechaFin": course[6]
            })
        })
    
    def get_by_literal(self, grade: str, section: str) -> Curso:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Curso\" WHERE \"Grado\"=%s AND \"Seccion\"=%s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (grade, section))
        course = cursor.fetchone()
        cursor.close()

        if not course or len(course) < 1:
            raise EntityNotFound(f"Curso no encontrado")
        
        return Curso({
            "CursoId": course[0],
            "Grado": course[1],
            "Seccion": course[2]
        })
    def update(self, model: Curso):
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"Curso\" SET"
        values = list()

        for key, value in model.to_dict().items():
            if value and key != "CursoId":
                sql += f" \"{key}\"=%s,"
                values.append(value)

        sql = sql[:-1] + f" WHERE \"CursoId\"=%s"
        values.append(model.id)
        self.logger.info(sql)
        cursor.execute(sql, tuple(values))
        affected = cursor.rowcount
        self.logger.debug(f"Affected {affected} rows")

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"Curso\" entity: {values}. Not commmit.")
            return False

        self.db_connection.commit()
        return True
    
    def delete(self, id):
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"Curso\" SET \"Activo\"=FALSE WHERE \"CursoId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        affected = cursor.rowcount
        cursor.close()
        self.db_connection.commit()
        return affected > 0
    
    def list(self, limit, offset):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM listar_cursos(%s,%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (offset or 0, limit or 5))
        rows = cursor.fetchall()
        cursor.close()

        return [Curso({
            "id": r[0],
            "Grado": r[1],
            "Seccion": r[2],
            "Capacidad": r[3],
            "PeriodoEscolar": PeriodoEscolar({
                "id": r[4]
            })
        }) for r in rows]
    
    def get_all_by_school_term(self, period_term_id: str) -> List[Curso]:
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM obtener_secciones_por_periodo_escolar(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (period_term_id,))
            rows = cursor.fetchall()
            cursor.close()

            self.logger.debug(rows, "Course rows")

            return [{
                "Grado": r[0],
                "Seccion": r[1],
                "Cantidad": r[2]
            } for r in rows]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_all_sections(self, period_term_id: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM obtener_secciones_por_periodo_escolar(%s);"
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def add(self, model: Curso) -> str:
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM agregar_curso(%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.grado, model.capacidad))
            course_id: str = cursor.fetchone()[0]
            cursor.close()
            self.db_connection.commit()
            return course_id
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def add_many(self, model: List[Curso]):
        try:
            cursor = self.db_connection.cursor()
            sql = ""
            params = []
            for c in model:
                sql += "SELECT * FROM agregar_curso(%s,%s);"
                params += [c.grado, c.capacidad]
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, tuple(params))
            cursor.close()
            self.db_connection.commit()
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def create_student_course(self, model: CursoEstudiante):
        try:
            cursor = self.db_connection.cursor()
            sql = "CALL agregar_curso_estudiante(%s,%s,%s);"
            cursor.execute(sql, model.to_tuple())
            cursor.close()
            self.db_connection.commit()
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_max_section(self, period_term_id: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT MAX(\"Seccion\"), COUNT(*), c.\"CursoId\", c.\"Grado\", p.\"CapacidadSecciones\" FROM \"CursoEstudiante\" AS ce INNER JOIN \"Curso\" AS c ON ce.\"CursoId\"=c.\"CursoId\" INNER JOIN \"PeriodoEscolar\" AS p ON p.\"PeriodoEscolarId\"=ce.\"PeriodoEscolarId\" WHERE ce.\"PeriodoEscolarId\"=%s GROUP BY c.\"CursoId\", c.\"Grado\", p.\"CapacidadSecciones\" ORDER BY c.\"Grado\";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (period_term_id,))
            max_section = cursor.fetchall()
            cursor.close()
            self.logger.debug(max_section, "Max section")

            return [{
                "Seccion": c[0],
                "Estudiantes": c[1],
                "CursoId": c[2],
                "Grado": c[3],
                "Capacidad": c[4],
            } for c in max_section]
        except Exception as err:
            self.db_connection.rollback()
            raise err
