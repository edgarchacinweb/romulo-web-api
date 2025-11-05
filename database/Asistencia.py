import database.connection
from database.repository import Repository
from models.Asistencia import Asistencia
from utils.logger import Logger
from typing import List


class AsistenciaRep():
    def __init__(self):
        self.db_connection = database.connection.Connection().get_connection()
        self.logger = Logger()

    def create(self, model: List[Asistencia]):
        try:
            cursor = self.db_connection.cursor()
            sql = "".join(["CALL registrar_asistencia(%s,%s,%s);" for _ in range(len(model))])
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, sum([m.to_tuple() for m in model], ()))
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()

            return affected
        except Exception as e:
            self.db_connection.rollback()
            raise e
