from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from models.Docente import Docente
from models.DatosPersona import DatosPersona
from models.Materia import Materia
from utils.exceptions import *

class DocenteRep(Repository):
    def __init__(self):
        self.logger = Logger()
        self.db_connection = Connection().get_connection()

    def create(self, model: Docente):
        cursor = self.db_connection.cursor()
        sql = "INSERT INTO \"Docente\" (\"DatosPersonaId\", \"MateriaId\") VALUES (%s,%s) RETURNING \"DocenteId\""
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
        sql = "SELECT * FROM obtener_docente_por_id(%s)"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        cursor.close()

        if not data or len(data) < 1:
            raise EntityNotFound(f"No se encontro el siguiente registro: {id}")

        return Docente(
            data[0],
            DatosPersona(data[1], data[2], data[3], data[4], data[5], data[6]),
            Materia(data[7], data[8])
        )

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_docentes();"
            self.logger.debug(sql)
            cursor.execute(sql)
            teachers = cursor.fetchall()
            cursor.close()

            return [
                Docente({
                    "id": t[0],
                    "DatosPersona": DatosPersona(t[1:9]),
                    "Materia": Materia(t[9:11]),
                    "Activo": t[11]
                }) for t in teachers
            ]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def list(self, limit, offset, filters):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT u.\"DatosPersona\", dp.\"Nombre\", dp.\"Apellido\", dp.\"Sexo\", dp.\"Cedula\", dp.\"Telefono\", dp.\"Direccion\", dp.\"Ocupacion\", string_agg(m.\"Nombre\", ',') AS \"Materias\" FROM \"Usuario\" AS u"
            sql += " INNER JOIN \"DatosPersona\" as dp ON dp.\"DatosPersonaId\"=u.\"DatosPersona\""
            sql += " LEFT JOIN \"Docente\" AS d ON d.\"DatosPersonaId\"=u.\"DatosPersona\""
            sql += " LEFT JOIN \"Materia\" AS m ON m.\"MateriaId\"=d.\"MateriaId\""
            sql += " WHERE u.\"Rol\"='docente'"

            if "Nombre" in filters:
                sql += f" AND dp.\"Nombre\" ILIKE '%{filters['Nombre']}%'"
            if "Apellido" in filters:
                sql += f" AND dp.\"Apellido\" ILIKE '%{filters['Apellido']}%'"
            if "Sexo" in filters:
                sql += f" AND dp.\"Sexo\"='{filters['Sexo']}'"
            if "Cedula" in filters:
                sql += f" AND dp.\"Cedula\"={filters['Cedula']}"
            if "Telefono" in filters:
                sql += f" AND dp.\"Telefono\"='{filters['Telefono']}'"

            sql += " GROUP BY u.\"DatosPersona\", dp.\"Nombre\", dp.\"Apellido\", dp.\"Cedula\", dp.\"Sexo\", dp.\"Telefono\", dp.\"Direccion\", dp.\"Ocupacion\""

            if "Materia" in filters:
                sql += f"HAVING string_agg(m.\"Nombre\", ',') ILIKE '%{filters['Materia']}%'"

            sql += f" LIMIT {limit or 5} OFFSET {offset or 0}"


            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            return [
                Docente({
                    "DatosPersona": DatosPersona(t[0:8]),
                    "Materias": t[8].split(',') if t[8] != None else list()
                }) for t in data
            ]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def update(self, model: Docente):
        try:
            cursor = self.db_connection.cursor()
            sql = "UPDATE \"Docente\" SET"
            values = list()

            for key, value in model.to_dict().items():
                if value and key != "DocenteId":
                    sql += f" \"{key}\"=%s,"
                    values.append(value)

            sql = sql[:-1] + f" WHERE \"DocenteId\"=%s"
            values.append(model.id)
            self.logger.info(sql)
            cursor.execute(sql, tuple(values))
            affected = cursor.rowcount
            self.logger.debug(f"Affected {affected} rows")

            if affected < 1:
                self.logger.warning(f"not rows affected to try update record in \"Docente\" entity: {values}. Not commmit.")
                return False

            self.db_connection.commit()
            return True
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def delete(self, identity: str):
        cursor = self.db_connection.cursor()
        sql = "CALL eliminar_docente(%s)"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (identity,))
        cursor.close()
        self.db_connection.commit()

    def add_subject(self, ci: str, subject_name: str) -> str:
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM agregar_materia_docente(%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (ci, subject_name))
            self.db_connection.commit()
            teacher_id = cursor.fetchone()[0]
            cursor.close()

            if not teacher_id:
                raise InsertEntityError(f"No se pudo agregar la materia al docente")

            return teacher_id
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def remove_subject(self, ci: str, subject_name: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "CALL eliminar_materia_docente(%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (ci, subject_name))
            self.db_connection.commit()
            cursor.close()
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def count(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT COUNT(*) FROM \"Usuario\" WHERE \"Rol\"='docente';"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            data = cursor.fetchone()
            cursor.close()
            return data[0]
        except Exception as err:
            self.db_connection.rollback()
            raise err
