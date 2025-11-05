from database.repository import Repository
from database.connection import Connection
from models.PeriodoEscolar import PeriodoEscolar
from models.BloqueHorario import BloqueHorario
from utils.logger import Logger
from utils.exceptions import *
from typing import List


class BloqueHorarioRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: BloqueHorario):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"BloqueHorario\" (\"HoraInicio\", \"HoraInicio\") VALUES (%s,%s) RETURNING \"BloqueHorarioId\";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
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

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"BloqueHorario\" WHERE \"Activo\"=true;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            blocks = cursor.fetchall()
            cursor.close()

            return [BloqueHorario({
                "id": b[0],
                "HoraInicio": b[1],
                "HoraFin": b[2]
            }) for b in blocks]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def delete(self, id):
        pass

    def update(self, model):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"BloqueHorario\" SET \"HoraInicio\"=%s, \"HoraFin\"=%s WHERE \"BloqueHorarioId\"=%s;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as err:
            self.db_connection.rollback()
            raise err
