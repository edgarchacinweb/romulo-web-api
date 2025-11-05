from database.repository import Repository
from database.connection import Connection
from models.Materia import Materia
from utils.logger import Logger
from utils.validations import Validations
from utils.exceptions import *

class MateriaRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Materia):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"Materia\" (\"Nombre\") VALUES (%s) RETURNING \"MateriaId\""
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.name, ))
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
        sql = "SELECT * FROM \"Materia\" WHERE \"MateriaId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id, ))
        materia = cursor.fetchone()
        cursor.close()

        if not materia or len(materia) < 1:
            raise EntityNotFound(f"No se encontraron datos de la materia: {id}")
        self.logger.success(f"Se seleccionaron los datos de la materia con ID: {id}")
        return Materia(materia)

    def list(self, limit, offset):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM \"Materia\" WHERE \"Activo\"=TRUE OFFSET %s LIMIT %s", (offset or 0, limit or 5))
        rows = cursor.fetchall()
        cursor.close()

        if rows == None or len(rows) == 0:
            rows = list()

        return [Materia(r) for r in rows]

    def delete(self, id: str) -> bool:
        try:
            cursor = self.db_connection.cursor()
            sql = "CALL eliminar_materia(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            affected = cursor.rowcount
            self.db_connection.commit()
            cursor.close()
            return affected > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def update(self, model):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"Materia\" SET"
            values = list()
            
            for key, value in model.to_dict().items():
                if value and key != "MateriaId":
                    sql += f" \"{key}\"=%s,"
                    values.append(value)

            sql = sql[:-1] + f" WHERE \"MateriaId\"='{model.id}'"
            self.logger.info(sql)
            cursor.execute(sql, tuple(values))
            affected = cursor.rowcount
            self.logger.debug(f"Affected {affected} rows")

            if affected < 1:
                self.logger.warning(f"not rows affected to try update record in \"Materia\" entity: {values}. Not commmit.")
                return False
            
            self.db_connection.commit()
            return True
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def list_by_grade(self, grade: int):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_materias_por_grado(%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (grade, ))
        rows = cursor.fetchall()
        cursor.close()

        if rows == None or len(rows) == 0:
            raise EntityNotFound("No se encontraron materias")

        return [Materia({"id": r[0], "Nombre": r[1]}) for r in rows]
    