from database.connection import Connection
from database.repository import Repository
from utils.logger import Logger
from models.Clase import Clase
from models.Docente import Docente
from models.Curso import Curso
from models.Materia import Materia
from models.DatosPersona import DatosPersona
from models.PeriodoEscolar import PeriodoEscolar
from utils.exceptions import *
from typing import List

class ClaseRep(Repository):
    def __init__(self):
        self.db_connection = Connection().get_connection()
        self.logger = Logger()

    def create(self, model: Clase):
        try:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO \"Clase\" (\"DocenteId\", \"CursoId\", \"PeriodoEscolarId\", \"Seccion\") VALUES (%s, %s, %s, %s) RETURNING \"ClaseId\";"
            cursor.execute(sql, model.to_tuple())
            id = cursor.fetchone()[0]
            cursor.close()
            self.db_connection.commit()
            return id
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def update(self, model: Clase):
        pass

    def delete(self, id):
        pass

    def get(self, id):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Clase\" AS cl INNER JOIN \"Docente\" AS d ON d.\"DocenteId\"=cl.\"DocenteId\" INNER JOIN \"DatosPersona\" AS dp ON dp.\"DatosPersonaId\"=d.\"DatosPersonaId\" INNER JOIN \"Materia\" AS m ON m.\"MateriaId\"=d.\"MateriaId\" INNER JOIN \"Curso\" AS c ON c.\"CursoId\"=cl.\"CursoId\" WHERE cl.\"ClaseId\"=%s;"
            cursor.execute(sql, (id,))
            result = cursor.fetchone()
            cursor.close()

            if not result:
                raise EntityNotFound(f"No se encontró ninguna clase con ese identificador")

            return Clase({
                "id": result[0],
                "Docente": Docente({
                    "id": result[7],
                    "DatosPersona": DatosPersona({
                        "id": result[8],
                        "Nombre": result[13],
                        "Apellido": result[14],
                        "Sexo": result[15],
                        "Cedula": result[16],
                        "Telefono": result[17]
                    }),
                    "Materia": Materia({
                        "id": result[22],
                        "Nombre": result[23]
                    })
                }),
                "Curso": Curso({
                    "id": result[26],
                    "Grado": result[27]
                }),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": result[3],
                }),
                "Seccion": result[4],
                "Fecha": result[6]
            })
        except Exception as e:
            self.db_connection.rollback()
            raise e

    def list(self, limit, offset):
        pass

    def filter(self, model: Clase):
        try:
            cursor = self.db_connection.cursor()
            sql = "SELECT * FROM \"Clase\" AS cl INNER JOIN \"Docente\" AS d ON d.\"DocenteId\"=cl.\"DocenteId\" INNER JOIN \"DatosPersona\" AS dp ON dp.\"DatosPersonaId\"=d.\"DatosPersonaId\" INNER JOIN \"Materia\" AS m ON m.\"MateriaId\"=d.\"MateriaId\" INNER JOIN \"Curso\" AS c ON c.\"CursoId\"=cl.\"CursoId\" INNER JOIN \"PeriodoEscolar\" AS pe ON pe.\"PeriodoEscolarId\"=cl.\"PeriodoEscolarId\" WHERE cl.\"Activo\"=TRUE"
            
            values = []
            if model.curso and model.curso.id:
                sql += " AND c.\"CursoId\"=%s"
                values.append(model.curso.id)
            if model.periodo_escolar and model.periodo_escolar.id:
                sql += " AND cl.\"PeriodoEscolarId\"=%s"
                values.append(model.periodo_escolar.id)
            if model.seccion:
                sql += " AND cl.\"Seccion\"=%s"
                values.append(model.seccion)
            if model.docente and model.docente.id:
                sql += " AND cl.\"DocenteId\"=%s"
                values.append(model.docente.id)
            
            sql += " ORDER BY c.\"Grado\", cl.\"Seccion\";"

            self.logger.debug(sql, "SQL")
            cursor.execute(sql, tuple(values))
            result = cursor.fetchall()
            cursor.close()
            
            return [Clase({
                "id": c[0],
                "Docente": Docente({
                    "id": c[7],
                    "DatosPersona": DatosPersona({
                        "id": c[8],
                        "Nombre": c[13],
                        "Apellido": c[14],
                        "Sexo": c[15],
                        "Cedula": c[16],
                        "Telefono": c[17]
                    }),
                    "Materia": Materia({
                        "id": c[22],
                        "Nombre": c[23]
                    })
                }),
                "Curso": Curso({
                    "id": c[26],
                    "Grado": c[27]
                }),
                "PeriodoEscolar": PeriodoEscolar({
                    "id": c[28],
                    "FechaInicio": c[29],
                    "FechaFin": c[30]
                }),
                "Seccion": c[4],
                "Fecha": c[32]
            }) for c in result]

        except Exception as e:
            self.db_connection.rollback()
            raise e
