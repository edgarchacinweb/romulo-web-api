from database.repository import Repository
from database.connection import Connection
from utils.logger import Logger
from utils.validations import Validations
from models.Usuario import Usuario
from utils.exceptions import InsertEntityError, InvalidId, EntityNotFound
from utils.config import bcrypt
from models.Usuario import Rol
from models.DatosPersona import DatosPersona
import os

class UsuarioRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Usuario):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"Usuario\" (\"Email\", \"Clave\", \"Rol\", \"DatosPersona\") VALUES (%s,%s,%s,%s) RETURNING \"UsuarioId\""
            self.logger.info(f"Usuario create query: {sql}")
            
            # ⚠️ AQUÍ ESTABA EL ERROR DE DOBLE ENCRIPTACIÓN. 
            # La línea que volvía a usar bcrypt.generate_password_hash fue eliminada,
            # ya que la contraseña ya viene encriptada desde el archivo users.py
            
            cursor.execute(sql, (model.email, model.password, model.role.value, model.DatosPersonaId))
            id = cursor.fetchone()[0]
            cursor.close()

            if not id:
                raise InsertEntityError(f"Error al guardar los datos del usuario")

            self.db_connection.commit()

            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def get(self, id):
        try:
            if not Validations.is_uuid(id):
                raise InvalidId(f"Identificador del usuario inválido")
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Usuario\" WHERE \"UsuarioId\"=%s";
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            user = cursor.fetchone()
            cursor.close()

            if user is None or len(user) < 1:
                raise EntityNotFound(f"Usuario no encontrado")
            
            self.logger.success(f"\"DatosPersona\" record with ID {id} was selected")
            return Usuario(user)
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def get_role(self, id: str):
        cursor = self.db_connection.cursor()
        sql = "SELECT \"Rol\" FROM \"Usuario\" WHERE \"UsuarioId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        rol = cursor.fetchone()[0]
        cursor.close()
        return rol

    def get_by_email(self, email: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Usuario\" WHERE \"Email\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (email.lower(),))
            result = cursor.fetchone()
            cursor.close()
            self.logger.debug(result, "result")
            if result:
                self.logger.debug(result)
                return Usuario(result)
            else:
                return None
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def list(self):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Usuario\" INNER JOIN \"DatosPersona\" ON \"DatosPersona\".\"DatosPersonaId\" = \"Usuario\".\"DatosPersona\" LIMIT %s OFFSET %s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql)
        users = cursor.fetchall()
        cursor.close()

        return [Usuario(user) for user in users]
    
    def filter(self, limit, offset, filters: dict):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Usuario\" INNER JOIN \"DatosPersona\" ON \"DatosPersona\".\"DatosPersonaId\" = \"Usuario\".\"DatosPersona\""
        sql += f" WHERE \"Usuario\".\"Rol\"='{filters['Rol']}'"

        if "Nombre" in filters:
            sql += f" AND \"DatosPersona\".\"Nombre\" ILIKE '%{filters['Nombre']}%'"
        if "Apellido" in filters:
            sql += f" AND \"DatosPersona\".\"Apellido\" ILIKE '%{filters['Apellido']}%'"
        if "Cedula" in filters:
            sql += f" AND \"DatosPersona\".\"Cedula\"='{filters['Cedula']}'"
        if "Email" in filters:
            sql += f" AND \"Usuario\".\"Email\" ILIKE '%{filters['Email']}%'"

        # sql += f" LIMIT {limit or 5} OFFSET {offset or 0}"
        sql += "ORDER BY \"Usuario\".\"FechaCreacion\" DESC;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql)
        users = cursor.fetchall()
        cursor.close()

        return [Usuario({
            "id": u[0],
            "Email": u[1],
            "Rol": Rol.TEACHER if u[3] == "docente" else Rol.PARENT,
            "DatosPersonaId": u[4],
            "FechaCreacion": u[6],
            "DatosPersona": DatosPersona({
                "DatosPersonaId": u[7],
                "Nombre": u[8],
                "Apellido": u[9],
                "Sexo": u[10],
                "Cedula": u[11],
                "Telefono": u[12]
            })
        }) for u in users]
    
    def get_role_by_ci(self, ci: str):
        cursor = self.db_connection.cursor()
        sql = "SELECT \"Rol\" FROM \"Usuario\" INNER JOIN \"DatosPersona\" ON \"DatosPersona\".\"DatosPersonaId\" = \"Usuario\".\"DatosPersona\" WHERE \"Cedula\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (ci,))
        rol = cursor.fetchone()[0]
        cursor.close()

        if not rol:
            raise EntityNotFound("No se encontraron datos con esa cedula de identidad")

        return Rol[rol]

    def delete(self, id):
        pass

    def update(self, id, model):
        pass

    def get_by_people_id(self, id: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT \"UsuarioId\" FROM \"Usuario\" WHERE \"DatosPersona\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Exception as e:
            self.db_connection.rollback()
            raise e