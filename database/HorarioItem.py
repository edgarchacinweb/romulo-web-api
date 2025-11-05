from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from utils.exceptions import *
from models.HorarioItem import HorarioItem
from models.Docente import Docente
from models.Curso import Curso
from models.DatosPersona import DatosPersona
from models.Materia import Materia
from typing import List

class HorarioItemRep(Repository):
    def __init__(self):
        self.logger = Logger()
        self.db_connection = Connection().get_connection()

    def create(self, model: HorarioItem):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"HorarioItem\" (\"BloqueHorarioId\",\"Dia\",\"DocenteId\",\"Actividad\",\"HorarioId\") VALUES (%s,%s,%s,%s,%s) RETURNING \"HorarioItemId\";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
            self.db_connection.commit()
            id = cursor.fetchone()[0]
            cursor.close()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def get(self, id:str) -> HorarioItem:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_horarios(%s)"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        schedule = cursor.fetchall()
        cursor.close()
        schedules = list()
        self.logger.debug(schedule, "Schedule rows")
        for s in schedule:
            data = {
                "id": s[0],
                "HoraInicio": s[1],
                "HoraFin": s[2],
                "Dia": s[3],
                "Actividad": s[4],
                "Docente": Docente(
                    s[5], DatosPersona(s[6], s[7], s[8], s[9], s[10], s[11]),
                    Materia(s[15], s[16])
                ) if s[5] else None,
                "Curso": Curso(s[12], s[13], s[14])
            }
            schedules.append(HorarioItem(data))

        if schedule:
            return schedules
        else:
            raise EntityNotFound(f"No se encontró ningún Horario con el id {id}")
        
    def get_all(self, HorarioId: str) -> List[HorarioItem]:
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM obtener_horario(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (HorarioId,))
            data = cursor.fetchall()
            cursor.close()
            return [HorarioItem({
                "id": h[0],
                "Actividad": h[1],
                "Dia": h[2],
                "Docente": Docente({
                    "DatosPersona": DatosPersona({
                        "Nombre": h[3],
                        "Apellido": h[4],
                    }),
                    "Materia": Materia({
                        "Nombre": h[5]
                    }),
                    id: h[6]
                })
            }) for h in data]
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def update(self, model: HorarioItem):
        try:
            cursor = self.db_connection.cursor()
            sql = "CALL actualizar_elemento_horario(%s,%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.Docente.id, model.id, model.Actividad))
            self.db_connection.commit()
            return True
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def delete(self, id):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"HorarioItem\" SET \"Activo\"=FALSE"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e
        
    def delete_row(self, id, start_time, end_time):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"HorarioItem\" SET \"Activo\"=FALSE WHERE \"HorarioId\"=%s AND \"HoraInicio\"=%s AND \"HoraFin\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id, start_time, end_time))
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def list(self, limit, offset):
        pass
