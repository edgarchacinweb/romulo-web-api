from database.connection import Connection
from models.Nota import Nota
from models.Materia import Materia
from models.Boleta import Boleta
from utils.logger import Logger
from utils.exceptions import *
from database.repository import Repository
from typing import List

class NotaRep(Repository):
    def __init__(self):
        self.logger = Logger()
        self.db_connection = Connection().get_connection()

    def create(self, model: Nota):
        cursor = self.db_connection.cursor()
        sql = "INSERT INTO \"Nota\" (\"Ponderacion\", \"Lapso\", \"MateriaId\", \"BoletaId\") VALUES (%s, %s, %s, %s) RETURNING \"NotaId\";"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, model.to_tuple())
        id = cursor.fetchone()[0]
        cursor.close()

        if not id:
            raise InsertEntityError("No se pudo insertar la Nota en la base de datos")
        
        self.db_connection.commit()
        return id

    def get(self, id):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Nota\" WHERE \"NotaId\" = %s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        nota = cursor.fetchone()
        cursor.close()
        calification = Nota({
            "NotaId": nota[0],
            "Ponderacion": nota[1],
            "Lapso": nota[2],
            "Materia": Materia({"MateriaId": nota[3]}),
            "Boleta": Boleta({"BoletaId": nota[4]})
        })

        return calification

    def list(self, limit, offset):
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Nota\" INNER JOIN \"Materia\" ON \"Materia\".\"MateriaId\" = \"Nota\".\"MateriaId\" ORDER BY \"Lapso\" LIMIT %s OFFSET %s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (limit, offset))
        notas = cursor.fetchall()
        cursor.close()
        califications = []
        for nota in notas:
            calification = Nota({
                "NotaId": nota[0],
                "Ponderacion": nota[1],
                "Lapso": nota[2],
                "Materia": Materia({"id": nota[3], "Nombre": nota[6]}),
                "Boleta": Boleta({"id": nota[4]})
            })
            califications.append(calification)

        return califications
    
    def list_by_student_and_grade(self, grade: int, student_id: str) -> List[Nota]:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_notas_por_grado_boleta(%s,%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (grade, student_id))
        califications = cursor.fetchall()
        cursor.close()

        if not data or len(data) == 0:
            raise EntityNotFound("No se encontraron notas para el estudiante")

        data = [
            Nota({
                "NotaId": c[0],
                "Ponderacion": c[1],
                "Lapso": c[2],
                "Materia": Materia({"Nombre": c[3]})
            }) for c in califications
        ]

        return data

    def list_by_schedule(self, schedule_id: str) -> List[Nota]:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM obtener_notas_por_boleta(%s);"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (schedule_id,))
        califications = cursor.fetchall()
        cursor.close()
        data = [
            Nota({
                "NotaId": c[0],
                "Ponderacion": c[1],
                "Lapso": c[2],
                "Materia": Materia({"Nombre": c[3]})
            }) for c in califications
        ]

        return data

    def update(self, model):
        cursor = self.db_connection.cursor()
        sql = "UPDATE \"Nota\" SET \"Ponderacion\"=%s WHERE \"NotaId\"=%s;"
        self.logger.info(sql)
        cursor.execute(sql, (model.ponderacion, model.id))
        affected = cursor.rowcount
        self.logger.debug(f"Affected {affected} rows")

        if affected < 1:
            self.logger.warning(f"not rows affected to try update record in \"Nota\" entity")
            return False
        
        self.db_connection.commit()
        return True

    def delete(self, id):
        cursor = self.db_connection.cursor()
        sql = "DELETE FROM \"Nota\" WHERE \"NotaId\" = %s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (id,))
        affected = cursor.rowcount
        cursor.close()
        self.db_connection.commit()
        return affected > 0

    def already_exists(self, subject_id: str, lapse: int, report_card_id: str) -> bool:
        cursor = self.db_connection.cursor()
        sql = "SELECT * FROM \"Nota\" WHERE \"MateriaId\" = %s AND \"Lapso\" = %s AND \"BoletaId\" = %s;"
        self.logger.debug(sql, "SQL")
        cursor.execute(sql, (subject_id, lapse, report_card_id))
        califications = cursor.fetchall()
        cursor.close()
        return len(califications) > 0
