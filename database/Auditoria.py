import database.connection
from models.Auditoria import Auditoria
from models.Usuario import Usuario, Rol
from utils.logger import Logger

class AuditoriaRep():
    def __init__(self):
        self.db_connection = database.connection.Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Auditoria):
        try:
            cursor = self.db_connection.cursor()

            if not model.usuario:
                cursor.execute("SELECT \"UsuarioId\" FROM \"Usuario\" WHERE \"Rol\"=%s;", (Rol.ADMIN.value, ))
                model.usuario = Usuario({"id": cursor.fetchone()[0]})

            sql = "INSERT INTO \"Auditoria\" (\"UsuarioId\", \"Descripcion\", \"Accion\") VALUES (%s, %s, %s) RETURNING \"AuditoriaId\";"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, model.to_tuple())
            self.db_connection.commit()
            id = cursor.fetchone()[0]
            cursor.close()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def filter(self, model: Auditoria, date_from, date_to):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT a.\"AuditoriaId\", a.\"Descripcion\", a.\"Accion\", a.\"FechaCreacion\", u.\"UsuarioId\", u.\"Email\", u.\"Rol\" FROM \"Auditoria\" AS a INNER JOIN \"Usuario\" AS u ON a.\"UsuarioId\" = u.\"UsuarioId\""
            data = list()
            values = list()

            if model.usuario and model.usuario.role:
                data.append("u.\"Rol\"=%s")
                values.append(model.usuario.role.value)
            if model.accion:
                data.append("a.\"Accion\"=%s")
                values.append(model.accion)
            if date_from and date_to:
                data.append("a.\"FechaCreacion\" BETWEEN %s AND %s")
                values.append(date_from)
                values.append(date_to)

            if data:
                sql += " WHERE " + " AND ".join(data)
            sql += " ORDER BY a.\"FechaCreacion\" DESC"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, tuple(values))
            records = cursor.fetchall()
            cursor.close()

            return [Auditoria({
                "id": record[0],
                "Descripcion": record[1],
                "Accion": record[2],
                "Fecha": record[3],
                "Usuario": Usuario({
                    "id": record[4],
                    "Email": record[5],
                    "Rol": Rol(record[6]),
                })
            }) for record in records]
            
        except Exception as e:
            self.db_connection.rollback()
            raise e
