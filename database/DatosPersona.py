from database.repository import Repository
from database.connection import Connection
from models.DatosPersona import DatosPersona
from utils.logger import Logger
from utils.validations import Validations
from utils.exceptions import EntityNotFound
import utils.exceptions as EntityExceptions

class DatosPersonaRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: DatosPersona):
        try:
            cursor = self.db_connection.cursor()

            if model.phone:
                cursor.execute(
                    "INSERT INTO \"DatosPersona\" (\"Nombre\", \"Apellido\", \"Sexo\", \"Cedula\", \"Telefono\", \"Direccion\", \"Ocupacion\") VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING \"DatosPersonaId\"",
                    (model.first_name, model.last_name, model.gender, model.ci, model.phone, model.direccion, model.ocupacion)
                )
            else:
                cursor.execute(
                    "INSERT INTO \"DatosPersona\" (\"Nombre\", \"Apellido\", \"Sexo\", \"Cedula\", \"Direccion\", \"Ocupacion\") VALUES (%s, %s, %s, %s, %s, %s) RETURNING \"DatosPersonaId\"",
                    (model.first_name, model.last_name, model.gender, model.ci, model.direccion, model.ocupacion)
                )
            id = cursor.fetchone()[0]
            self.logger.debug(id)
            cursor.close()
            self.db_connection.commit()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def get(self, id):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM \"DatosPersona\" WHERE \"DatosPersonaId\"=%s", (id,))
        user = cursor.fetchone()
        cursor.close()
        if not user or len(user) < 1:
            raise EntityExceptions.EntityNotFound("No \"DatosPersona\" found with ID: {id}")
        self.logger.success(f"\"DatosPersona\" record with ID {id} was selected")
        self.logger.info(user)
        return DatosPersona(user)

    def list(self, limit, offset):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM \"DatosPersona\" OFFSET %s LIMIT %s", (offset or 0, limit or 5))
        rows = cursor.fetchall()
        cursor.close()
        if rows == None or len(rows) == 0:
            raise EntityExceptions.EntityNotFound("No se encontraron datos")
        return [DatosPersona(r) for r in rows]

    def delete(self, id):
        if not Validations.is_uuid(id):
            raise EntityExceptions.InvalidId(f"Invalid ID for entity \"DatosPersona\": {id}")
        
        cursor = self.db_connection.cursor()
        cursor.execute(f"DELETE FROM \"DatosPersona\" WHERE \"DatosPersonaId\"='{id}'")
        affected = cursor.rowcount

        if affected == 0:
            return False
        
        self.db_connection.commit()
        return True

    def update(self, model):
        self.logger.debug(model.id, "Model ID")
        if not Validations.is_uuid(model.id):
            raise EntityExceptions.InvalidId(f"Invalid ID for entity \"DatosPersona\": {id}")
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"DatosPersona\" SET"
        values = list()
        
        for key, value in model.to_dict().items():
            if value and key != "DatosPersonaId":
                sql += f" \"{key}\"=%s,"
                values.append(value)

        sql = sql[:-1] + f" WHERE \"DatosPersonaId\"='{model.id}'";
        self.logger.info(sql)
        cursor.execute(sql, tuple(values))
        affected = cursor.rowcount
        self.logger.debug(f"Affected {affected} rows")

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"DatosPersona\" entity: {values}. Not commmit.")
            return False
        
        self.db_connection.commit()
        return True

    def get_by_user(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT \"DatosPersona\" FROM \"Usuario\" WHERE \"UsuarioId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        cursor.close()

        if not data:
            return None
        else:
            return data[0]
    
    def get_by_ci(self, ci: int, exception: bool = True):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"DatosPersona\" WHERE \"Cedula\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (ci,))
        data = cursor.fetchone()
        cursor.close()

        self.logger.debug(data, "Database/DatosPersona.py: get_by_ci()")

        if not data and exception:
            raise EntityNotFound("No se encontraron datos con esa cédula de identidad")
        elif not data:
            return None
        
        return DatosPersona({
            "id": data[0],
            "Nombre": data[1],
            "Apellido": data[2],
            "Sexo": data[3],
            "Cedula": data[4],
            "Telefono": data[5],
            "Direccion": data[6],
            "Ocupacion": data[7]
        });
