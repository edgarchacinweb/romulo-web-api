from database.connection import Connection
from database.repository import Repository
from models.PeriodoEscolar import PeriodoEscolar
from utils.logger import Logger
from utils.exceptions import *

class PeriodoEscolarRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: PeriodoEscolar):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"PeriodoEscolar\" (\"FechaInicio\",\"FechaFin\", \"CapacidadSecciones\") VALUES (%s,%s, %s) RETURNING \"PeriodoEscolarId\""
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.fecha_inicio, model.fecha_fin, model.capacidad))
            id = cursor.fetchone()[0]
            cursor.close()

            if not id:
                raise InsertEntityError(f"No se pudo insertar el siguiente registro: {model.to_dict()}")

            self.db_connection.commit()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"PeriodoEscolar\" WHERE \"PeriodoEscolarId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        periodo = cursor.fetchone()
        cursor.close()

        if not periodo or len(periodo) < 1:
            raise EntityNotFound(f"No se encontro el siguiente registro: {id}")

        return PeriodoEscolar({
            "id": periodo[0],
            "FechaInicio": periodo[1],
            "FechaFin": periodo[2],
            "Capacidad": periodo[3],
            "FechaCreacion": periodo[4]
        })
    
    def get_latest(self):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"PeriodoEscolar\" WHERE \"Activo\"=TRUE AND CURRENT_DATE <= \"FechaFin\" ORDER BY \"FechaInicio\" DESC LIMIT 1"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql)
        periodo = cursor.fetchone()
        cursor.close()

        if not periodo or len(periodo) < 1:
            raise EntityNotFound(f"No se encontró ningún registro")

        return PeriodoEscolar({
            "id": periodo[0],
            "FechaInicio": periodo[1],
            "FechaFin": periodo[2],
            "Capacidad": periodo[3],
            "FechaCreacion": periodo[4]
        })

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"PeriodoEscolar\" WHERE \"Activo\"=TRUE ORDER BY \"FechaInicio\" DESC;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            periods = cursor.fetchall()
            cursor.close()

            return [PeriodoEscolar({
                "id": p[0],
                "FechaInicio": p[1],
                "FechaFin": p[2],
                "Capacidad": p[3],
                "FechaCreacion": p[4]
            }) for p in periods]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def list(self, limit, offset) -> list[PeriodoEscolar]:
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_periodos_escolares(%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (offset or 0, limit or 10))
            periods = cursor.fetchall()
            cursor.close()

            return [PeriodoEscolar({
                "id": p[0],
                "FechaInicio": p[1],
                "FechaFin": p[2],
                "Capacidad": p[3],
                "FechaCreacion": p[4]
            }) for p in periods]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def delete(self, id):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"PeriodoEscolar\" SET \"Activo\"=FALSE WHERE \"PeriodoEscolarId\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def update(self, model: PeriodoEscolar):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"PeriodoEscolar\" SET \"FechaInicio\"=%s, \"FechaFin\"=%s, \"CapacidadSecciones\"=%s WHERE \"PeriodoEscolarId\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.fecha_inicio, model.fecha_fin, model.capacidad, model.id))
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as err:
            self.db_connection.rollback()
            raise err
