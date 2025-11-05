from database.repository import Repository
from database.connection import Connection
from models.PeriodoEscolar import PeriodoEscolar
from models.DatosPersona import DatosPersona
from models.Estudiante import Estudiante
from models.Boleta import Boleta
from utils.logger import Logger
from utils.exceptions import *
from typing import List

class BoletaRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Boleta):
        cursor = self.db_connection.cursor()
        sql = "INSERT INTO \"Boleta\" (\"EstudianteId\",\"CursoId\",\"PeriodoEscolarId\") VALUES (%s, %s) RETURNING \"BoletaId\";"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, model.to_tuple())
        id = cursor.fetchone()[0]
        cursor.close()

        if not id:
            raise InsertEntityError(f"No se pudo insertar el siguiente registro: {model.to_dict()}")
        
        self.db_connection.commit()
        return id

    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_boleta_por_id(%s)"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        record = cursor.fetchone()
        cursor.close()

        if not record or len(record) == 0:
            raise EntityNotFound(f"No se encontraron datos de la boleta buscada")

        self.logger.debug(record[8:])

        return Boleta({
            "BoletaId": record[0],
            "Estudiante": Estudiante({
                "id":record[1],
                "DatosPersona": DatosPersona(record[2:8]),
                "Activo": record[8]
            }),
            "PeriodoEscolar": PeriodoEscolar({
                "id": record[9],
                "FechaInicio": record[10],
                "FechaFin": record[11]
            })
        })

    def list(self, limit, offset) -> List[Boleta]:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM listar_boletas(%s,%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (offset or 0, limit or 5))
        records = cursor.fetchall()
        cursor.close()

        if not records or len(records) == 0:
            raise EntityNotFound(f"No se encontraron boletas")

        schedules = [
            Boleta({
                "BoletaId": record[0],
                "Estudiante": Estudiante({
                    "id":record[1],
                    "DatosPersona": DatosPersona(record[2:8]),
                    "Activo": record[8]
                }),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": record[9],
                    "FechaInicio": record[10],
                    "FechaFin": record[11],
                })
            }) for record in records
        ]

        return schedules

    def delete(self, id):
        cursor = self.db_connection.cursor()
        sql = "DELETE FROM \"Nota\" WHERE \"BoletaId\" = %s;DELETE FROM \"Boleta\" WHERE \"BoletaId\" = %s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,id))
        affected_rows = cursor.rowcount
        cursor.close()
        self.db_connection.commit()
        return affected_rows > 0

    def update(self, model):
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"Boleta\" SET"
        values = list()

        for key, value in model.to_dict().items():
            if value and key != "BoletaId":
                sql += f" \"{key}\"=%s,"
                values.append(value)

        sql = sql[:-1] + f" WHERE \"BoletaId\"=%s"
        values.append(model.id)
        self.logger.info(sql)
        cursor.execute(sql, tuple(values))
        affected = cursor.rowcount
        self.logger.debug(f"Affected {affected} rows")

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"Boleta\" entity: {values}. Not commmit.")
            return False

        self.db_connection.commit()
        return True
