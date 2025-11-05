from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from models.Horario import Horario
from models.Curso import Curso
from models.Docente import Docente
from models.Materia import Materia
from models.DatosPersona import DatosPersona
from models.PeriodoEscolar import PeriodoEscolar
from utils.exceptions import *

class HorarioRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Horario):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM registrar_horario(%s, %s::SMALLINT);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
            schedule_id = cursor.fetchone()[0]
            cursor.close()

            if not schedule_id:
                raise InsertEntityError("No se pudo insertar el registro")
            
            self.db_connection.commit()
            return schedule_id
        except Exception as e:
            self.db_connection.rollback()
            raise e
        
    def get(self, id):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT h.\"HorarioId\", c.\"CursoId\", c.\"Grado\", pe.\"PeriodoEscolarId\", pe.\"FechaInicio\", pe.\"FechaFin\", h.\"Seccion\" FROM \"Horario\" AS h INNER JOIN \"Curso\" AS c ON c.\"CursoId\"=h.\"CursoId\" INNER JOIN \"PeriodoEscolar\" AS pe ON pe.\"PeriodoEscolarId\"=h.\"PeriodoEscolarId\";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            schedule = cursor.fetchone()
            cursor.close()

            return {
                "HorarioId": schedule[0],
                "Curso": Curso({
                    "id": schedule[1],
                    "Grado": schedule[2],
                }).to_dict(),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": schedule[3],
                    "FechaInicio": schedule[4],
                    "FechaFin": schedule[5]
                }).to_dict(),
                "Seccion": schedule[6]
            }
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_all_by_school_term(self, school_term_id):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_horarios_periodo_academico(%s);"
            self.logger.debug(sql, "SQL")
            self.logger.debug(school_term_id, "school_term_id")
            cursor.execute(sql, (school_term_id,))
            schedules = cursor.fetchall()
            cursor.close()

            return [{
                "HorarioId": s[0],
                "Curso": Curso({
                    "id": s[1],
                    "Grado": s[2],
                }).to_dict(),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": s[3],
                    "FechaInicio": s[4],
                    "FechaFin": s[5]
                }).to_dict(),
                "Seccion": s[7]
            } for s in schedules]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT \"PeriodoEscolarId\" FROM \"PeriodoEscolar\" WHERE \"Activo\"=TRUE ORDER BY \"FechaInicio\" DESC LIMIT 1"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            school_term_id = cursor.fetchone()[0]
            sql = "SELECT * FROM listar_horarios_periodo_academico(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (school_term_id,))
            schedules = cursor.fetchall()
            cursor.close()

            return [{
                "HorarioId": s[0],
                "Curso": Curso({
                    "id": s[1],
                    "Grado": s[2],
                }).to_dict(),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": s[3],
                    "FechaInicio": s[4],
                    "FechaFin": s[5]
                }).to_dict(),
                "Seccion": s[7]
            } for s in schedules]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def update(self, model):
        pass

    def delete(self, id):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"Horario\" SET \"Activo\"=FALSE WHERE \"HorarioId\"=%s;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            row_count = cursor.rowcount
            cursor.close()

            if row_count == 0:
                raise EntityUpdateError("Error al actualizar el registro")

            self.db_connection.commit()
            return row_count > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def list(self, limit, offset):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_horarios(%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (offset or 0, limit or 10))
            schedules = cursor.fetchall()
            cursor.close()
            
            return [Horario({
                "id": s[0],
                "Curso": Curso({
                    "id": s[1],
                    "Grado": s[2],
                    "Seccion": s[3],
                    "Capacidad": s[4],
                    "PeriodoEscolar": PeriodoEscolar({
                        "id": s[5],
                        "FechaInicio": s[6],
                        "FechaFin": s[7]
                    })
                }),
            }) for s in schedules]
        except Exception as e:
            self.db_connection.rollback()
            raise e
        
    def list_by_schedule(self, schedule_id):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_profesores_por_horario(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (schedule_id,))
            schedules = cursor.fetchall()
            cursor.close()

            return [Docente({
                "id": s[0],
                "DatosPersona": DatosPersona({
                    "id": s[1],
                    "Nombre": s[2],
                    "Apellido": s[3],
                    "Cedula": s[4],
                }),
                "Materia": Materia({
                    "id": s[5],
                    "Nombre": s[6]
                })
            }) for s in schedules]
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def filter(self, model: Horario):
        try:
            cursor = self.db_connection.cursor()
            values = [model.periodo_escolar.id]
            sql = "SELECT h.\"HorarioId\", h.\"CursoId\", c.\"Grado\", h.\"Seccion\" FROM \"Horario\" AS h INNER JOIN \"Curso\" AS c ON h.\"CursoId\"=c.\"CursoId\" WHERE h.\"PeriodoEscolarId\"=%s"

            if model.curso and model.curso.id:
                values.append(model.curso.id)
                sql += " AND c.\"CursoId\"=%s"
            if model.seccion:
                values.append(model.seccion)
                sql += " AND h.\"Seccion\"=%s"

            sql += ";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, tuple(values))
            schedules = cursor.fetchall()
            cursor.close()

            self.logger.debug(schedules, "schedules")
            return [Horario({
                "id": s[0],
                "Curso": Curso({
                    "id": s[1],
                    "Grado": s[2],
                }),
                "Seccion": s[3]
            }) for s in schedules]
        except Exception as e:
            self.db_connection.rollback()
            raise e
