from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from utils.exceptions import *
from models.Estudiante import Estudiante
from models.DatosPersona import DatosPersona
from models.Curso import Curso
from models.Clase import Clase
from models.Asistencia import Asistencia
from database.DatosPersona import DatosPersonaRep
from database.Curso import CursoRep


class EstudianteRep(Repository):
    def __init__(self):
        self.logger = Logger()
        self.db_connection = Connection().get_connection()
        self.datos_persona_rep = DatosPersonaRep()
        self.curso_rep = CursoRep()

    def create(self, model: Estudiante):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"Estudiante\" (\"FechaNacimiento\",\"DatosPersonaId\",\"RepresentanteId\") VALUES (%s,%s,%s) RETURNING \"EstudianteId\""
            self.logger.debug(sql, "SQL")
            self.logger.debug(model.to_tuple(), "Estudiante tuple")
            cursor.execute(sql, model.to_tuple())
            self.db_connection.commit()
            id = cursor.fetchone()[0]
            cursor.close()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def create_by_ci(self, model: Estudiante, parent_ci: int):
        try:
            cursor = self.db_connection.cursor()
            sql = "CALL crear_estudiante(%s,%s,%s,%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.birthdate, model.curso.id, model.datos_persona.id, parent_ci))
            self.db_connection.commit()
            affected = cursor.rowcount
            cursor.close()

            return affected > 0
        except Exception as e:
            self.db_connection.rollback()
            raise e
    
    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Estudiante\" WHERE \"EstudianteId\"=%s"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        cursor.close()

        if not data or len(data) < 1:
            raise EntityNotFound(f"No se encontro el siguiente registro: {id}")

        self.logger.debug(data, "SQL")

        student = Estudiante({
            "id": data[0],
            "FechaNacimiento": data[1],
        })
        student.datos_persona = self.datos_persona_rep.get(student.datos_persona.id)
        student.representante = self.datos_persona_rep.get(student.representante.id)

        return student
    
    def get_by_people(self, id: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Estudiante\" WHERE \"DatosPersonaId\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            cursor.close()

            if not data or len(data) < 1:
                raise EntityNotFound(f"No se encontro el siguiente registro: {id}")

            self.logger.debug(data, "SQL")
            student = Estudiante({
                "id": data[0],
                "FechaNacimiento": data[1],
            })
            self.logger.debug(student.datos_persona.id);
            student.datos_persona = self.datos_persona_rep.get(data[2])
            student.representante = self.datos_persona_rep.get(data[3])

            return student
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def get_all(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Estudiante\" INNER JOIN \"DatosPersona\" AS d ON d.\"DatosPersonaId\"=\"Estudiante\".\"DatosPersonaId\" INNER JOIN \"DatosPersona\" AS r ON r.\"DatosPersonaId\"=\"Estudiante\".\"RepresentanteId\" WHERE \"Estudiante\".\"Activo\"=TRUE;"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()

            return [{
                "EstudianteId": d[0],
                "FechaNacimiento": d[1],
                "DatosPersona": {
                    "DatosPersonaId": d[6],
                    "Nombre": d[7],
                    "Apellido": d[8],
                    "Sexo": d[9],
                    "Cedula": d[10]
                },
                "Representante": {
                    "DatosPersonaId": d[16],
                    "Nombre": d[17],
                    "Apellido": d[18],
                    "Sexo": d[19],
                    "Cedula": d[20],
                    "Telefono": d[21]
                }
            } for d in data]
        except Exception as err:
            self.db_connection.rollback()
            raise err

    def list(self, limit, offset):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM list_students(%s,%s)"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (limit, offset))
        data = cursor.fetchall()
        cursor.close()

        if not data or len(data) < 1:
            raise EntityNotFound(f"No se encontro el siguiente registro: {id}")

        estudiantes = []
        for student in data:
            estudiantes.append(Estudiante({
                "id": student[0],
                "FechaNacimiento": student[1],
                "Activo": student[2],
                "DatosPersona": DatosPersona(student[3:9]),
                "Representante": DatosPersona(student[9:15]),
                "Curso": Curso(student[15:18])
            }))

        return estudiantes

    def update(self, model: Estudiante):
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"Estudiante\" SET"
        values = list()

        for key, value in model.to_dict().items():
            if value and key != "EstudianteId":
                sql += f" \"{key}\"=%s,"
                values.append(value)

        sql = sql[:-1] + f" WHERE \"DocenteId\"=%s"
        values.append(model.id)
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, tuple(values))
        affected = cursor.rowcount
        cursor.close()

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"Estudiante\" entity: {values}. Not commmit.")
            return False

        self.db_connection.commit()
        return True
    
    def delete(self, id):
        cursor = self.db_connection.cursor()
        cursor.execute(f"DELETE FROM \"Estudiante\" WHERE \"EstudianteId\"=%s", (id,))
        affected = cursor.rowcount
        cursor.close()
        self.db_connection.commit()
        return affected > 0
    
    def create_with_parent(self, model: Estudiante, parent_ci: int) -> bool:
        cursor = self.db_connection.cursor()
        sql = "CALL crear_estudiante(%s,%s,%s,%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (model.birthdate, model.curso.id, model.datos_persona.id, parent_ci))
        self.db_connection.commit()
        affected = cursor.rowcount
        cursor.close()

        return affected > 0

    def list_by_parent(self, parent_id: str):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Estudiante\" INNER JOIN \"DatosPersona\" ON \"DatosPersona\".\"DatosPersonaId\"=\"Estudiante\".\"DatosPersonaId\" WHERE \"RepresentanteId\"=%s"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (parent_id,))
            data = cursor.fetchall()
            cursor.close()

            return [Estudiante({
                "id": d[0],
                "FechaNacimiento": d[1],
                "DatosPersona": DatosPersona({
                    "id": d[6],
                    "Nombre": d[7],
                    "Apellido": d[8],
                    "Sexo": d[9],
                    "Cedula": d[10]
                }),
                "RepresentanteId": d[3],
            }) for d in data]
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def list_by_class(self, model: Clase):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM listar_asistencias(%s);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql, (model.id,))
            data = cursor.fetchall()
            self.logger.debug(data, "Asistencia")
            cursor.close()

            return [Asistencia({
                "Estudiante": Estudiante({
                    "id": a[0],
                    "DatosPersona": DatosPersona({
                        "id": a[1],
                        "Nombre": a[2],
                        "Apellido": a[3],
                        "Sexo": a[4],
                        "Cedula": a[5]
                    }),
                }),
                "id": a[6],
                "Activo": a[7]
            }) for a in data]
        except Exception as err:
            self.db_connection.rollback()
            raise err
        
    def count(self):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT COUNT(\"EstudianteId\") FROM \"CursoEstudiante\" WHERE \"PeriodoEscolarId\"=(SELECT \"PeriodoEscolarId\" FROM \"PeriodoEscolar\" ORDER BY \"FechaInicio\" DESC LIMIT 1);"
            self.logger.debug(sql, "SQL")
            cursor.execute(sql)
            data = cursor.fetchone()
            cursor.close()
            return data[0];
        except Exception as err:
            self.db_connection.rollback()
            raise err
