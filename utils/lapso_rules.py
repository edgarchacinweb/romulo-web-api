from datetime import datetime, timedelta
from database.connection import Connection

class LapsoRules:
    @staticmethod
    def is_calification_open():
        conn = Connection().get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT l."LapsoId", l."Numero", l."FechaInicio", l."FechaFin" 
                FROM "Lapso" l
                JOIN "PeriodoEscolar" pe ON l."PeriodoEscolarId" = pe."PeriodoEscolarId"
                WHERE pe."Activo" = TRUE
                ORDER BY l."Numero" ASC LIMIT 3;
            ''')
            rows = cursor.fetchall()

            if len(rows) < 3:
                return {"is_open": False, "lapso_id": None}

            lapsos = {row[1]: {"id": row[0], "inicio": row[2], "fin": row[3]} for row in rows}
            today = datetime.now().date()
            
            # First Lapso
            fecha_apertura_1 = lapsos[1]["fin"] - timedelta(days=7)
            fecha_cierre_1 = lapsos[2]["inicio"]
            
            # Second Lapso
            fecha_apertura_2 = lapsos[2]["fin"] - timedelta(days=7)
            fecha_cierre_2 = lapsos[3]["inicio"]
            
            # Third Lapso
            fecha_apertura_3 = lapsos[3]["fin"] - timedelta(days=7)
            fecha_cierre_3 = lapsos[3]["fin"]
            
            # Las reglas dictan:
            # - Primer Lapso: Se ABRE exactamente 7 días antes del cierre del 1er lapso. Se CIERRA cuando inicia el 2do lapso.
            # - Segundo Lapso: Se ABRE exactamente 7 días antes del cierre del 2do lapso. Se CIERRA cuando inicia el 3er lapso.
            # - Tercer Lapso: Se ABRE exactamente 7 días antes del cierre del 3er lapso. Se CIERRA cuando finaliza el 3er lapso.

            res = {"is_open": False, "lapso_id": None}
            if fecha_apertura_1 <= today < fecha_cierre_1:
                res = {"is_open": True, "lapso_id": lapsos[1]["id"]}
            elif fecha_apertura_2 <= today < fecha_cierre_2:
                res = {"is_open": True, "lapso_id": lapsos[2]["id"]}
            elif fecha_apertura_3 <= today <= fecha_cierre_3:
                res = {"is_open": True, "lapso_id": lapsos[3]["id"]}
                
            try:
                with open("tmp_debug.txt", "w") as f:
                    f.write(f"Today: {today}\n")
                    f.write(f"Lapsos: {lapsos}\n")
                    f.write(f"L1: open_date={fecha_apertura_1}, close_date={fecha_cierre_1}\n")
                    f.write(f"L2: open_date={fecha_apertura_2}, close_date={fecha_cierre_2}\n")
                    f.write(f"L3: open_date={fecha_apertura_3}, close_date={fecha_cierre_3}\n")
                    f.write(f"Result: {res}\n")
            except:
                pass
                
            return res
            
        except Exception as e:
            try:
                with open("tmp_debug.txt", "w") as f:
                    f.write(f"Exception: {str(e)}\n")
            except:
                pass
            print("Error checking lapso rules", e)
            return {"is_open": False, "lapso_id": None}
        finally:
            cursor.close()
