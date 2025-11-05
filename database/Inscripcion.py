from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from utils.exceptions import *
from models.Inscripcion import Inscripcion

class InscripcionRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Inscripcion):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"Inscripcion\" (\"EstudianteId\",\"EstadoInscripcion\") RETURNING \"Inscripcion\""
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.to_tuple()))
            self.db_connection.commit()
            id = cursor.fetchone()[0]
            cursor.close()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def get(self, id):
        pass

    def list(self, limit, offset):
        pass

    def delete(self, id):
        pass

    def update(self, model):
        pass
