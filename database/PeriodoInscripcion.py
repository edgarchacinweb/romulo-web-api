from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from utils.exceptions import *
from models.PeriodoInscripcion import PeriodoInscripcion
from models.PeriodoEscolar import PeriodoEscolar

class PeriodoInscripcionRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: PeriodoInscripcion):
        cursor = self.db_connection.cursor()
        sql = "INSERT INTO \"PeriodoInscripcion\" (\"Inicio\",\"Fin\",\"PeriodoEscolarId\") VALUES (%s, %s, %s) RETURNING \"PeriodoInscripcion\""
        self.logger.debug(sql, "SQL")
        # self.logger.debug(model.to_tuple(), "PeriodoInscripcion tuple")
        cursor.execute(sql, model.to_tuple())
        id = cursor.fetchone()[0]
        cursor.close()

        if not id:
            raise InsertEntityError(f"The following record could not be inserted: {model.to_dict()}")

        self.db_connection.commit()
        return id

    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"PeriodoInscripcion\" WHERE \"PeriodoInscripcion\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        reg = cursor.fetchone()
        cursor.close()

        if not reg or len(reg) < 1:
            raise EntityNotFound("No \"PeriodoInscripcion\" found with ID: {id}")
        self.logger.success(f"\"PeriodoInscripcion\" record with ID {id} was selected")
        return PeriodoInscripcion({
            "id": reg[0],
            "Inicio": reg[1],
            "Fin": reg[2],
            "PeriodoEscolar": PeriodoEscolar({
                "id": reg[3]
            })
        })

    def list(self):
        cursor = self.db_connection.cursor()
        sql = "SELECT pi.\"PeriodoInscripcion\", pi.\"Inicio\", pi.\"Fin\", pi.\"FechaCreacion\", pe.\"PeriodoEscolarId\", pe.\"FechaInicio\", pe.\"FechaFin\", pi.\"Activo\" FROM \"PeriodoInscripcion\" AS pi INNER JOIN \"PeriodoEscolar\" AS pe ON pi.\"PeriodoEscolarId\"=pe.\"PeriodoEscolarId\";"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql)
        inscripciones = cursor.fetchall()
        cursor.close()

        return [PeriodoInscripcion({
            "id": inscripcion[0],
            "Inicio": inscripcion[1],
            "Fin": inscripcion[2],
            "FechaCreacion": inscripcion[3],
            "Activo": inscripcion[7],
            "PeriodoEscolar": PeriodoEscolar({
                "id": inscripcion[4],
                "FechaInicio": inscripcion[5],
                "FechaFin": inscripcion[6]
            })
        }) for inscripcion in inscripciones]

    def delete(self, id):
        cursor = self.db_connection.cursor()
        cursor.execute(f"UPDATE \"PeriodoInscripion\" SET \"Activo\"=FALSE WHERE \"PeriodoInscripcionId\"='{id}'")
        affected = cursor.rowcount
        cursor.close()
        self.db_connection.commit()
        return affected > 0

    def update(self, model):
        cursor = self.db_connection.cursor()
        updates = []
        values = []
        
        if model.start:
            updates.append("\"Inicio\"=%s")
            values.append(model.start)
        if model.end:
            updates.append("\"Fin\"=%s")
            values.append(model.end)
        if model.activo is not None:
            updates.append("\"Activo\"=%s")
            values.append(model.activo)
            
        if not updates:
            return False
            
        sql = "UPDATE \"PeriodoInscripcion\" SET " + ", ".join(updates) + " WHERE \"PeriodoInscripcion\"=%s"
        self.logger.info(sql)
        values.append(model.id)
        cursor.execute(sql, tuple(values))
        affected = cursor.rowcount
        self.logger.debug(f"Affected {affected} rows")

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"PeriodoInscripcion\" entity: {values}. Not commmit.")
            return False
        
        self.db_connection.commit()
        return True
    
    def get_latest(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"PeriodoInscripcion\" WHERE CURRENT_DATE <= \"Fin\" ORDER BY \"Inicio\" DESC LIMIT 1;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            inscripcion = cursor.fetchone()
            cursor.close()

            if not inscripcion or len(inscripcion) < 1:
                return PeriodoInscripcion({})
        
            return PeriodoInscripcion({
                "id": inscripcion[0],
                "Inicio": inscripcion[1],
                "Fin": inscripcion[2],
                "PeriodoEscolar": PeriodoEscolar({
                    "id": inscripcion[3]
                })
            })
        except Exception as err:
            self.db_connection.rollback()
            raise err
