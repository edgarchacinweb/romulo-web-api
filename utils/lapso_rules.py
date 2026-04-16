from datetime import datetime, timedelta
from database.connection import Connection

class LapsoRules:
    @staticmethod
    def get_open_lapsos_status():
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

            status = {
                "lapso1_abierto": False,
                "lapso2_abierto": False,
                "lapso3_abierto": False,
                "open_lapso_ids": [],
                "status": "CLOSED",
                "lapso": None
            }

            if len(rows) < 3:
                return status

            today = datetime.now().date()

            # Iterate through the 3 lapsos to check strictly: today >= (finish_date - 7 days)
            # Track the "most current" open lapso (highest Numero among open ones)
            current_open_lapso = None
            for row in rows:
                lapso_id = row[0]
                lapso_numero = row[1]
                fecha_inicio = row[2]
                fecha_fin = row[3]
                
                fecha_apertura = fecha_fin - timedelta(days=7)
                
                if today >= fecha_apertura:
                    status[f"lapso{lapso_numero}_abierto"] = True
                    status["open_lapso_ids"].append(lapso_id)
                    # Keep the most recently opened lapso as the active one
                    current_open_lapso = {
                        "LapsoId": str(lapso_id),
                        "Numero": lapso_numero,
                        "FechaInicio": fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None,
                        "FechaFin": fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None
                    }

            if current_open_lapso:
                status["status"] = "OPEN"
                status["lapso"] = current_open_lapso

            return status

        except Exception as e:
            print("Error checking lapso rules", e)
            return {
                "lapso1_abierto": False,
                "lapso2_abierto": False,
                "lapso3_abierto": False,
                "open_lapso_ids": [],
                "status": "CLOSED",
                "lapso": None
            }
        finally:
            cursor.close()
