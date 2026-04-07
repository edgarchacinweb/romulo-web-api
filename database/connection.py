import psycopg2
import os
from utils.logger import Logger
from datetime import datetime
from models.Auditoria import Auditoria
from database.Auditoria import AuditoriaRep

db_name = os.getenv("db_name")
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")

class Singleton():
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

class Connection(Singleton):
    def __init__(self):
        # Usamos un atributo para saber si ya inicializamos (solo la primera vez)
        if not hasattr(self, '_initialized'):
            self.conn = None
            self.logger = Logger() # O la lógica para tu Logger
            self._initialized = True # Marcamos como inicializado

    def get_connection(self):
        if self.conn is None:
            self.logger = Logger()
            try:
                self.conn = psycopg2.connect(
                    dbname=db_name,
                    user=db_user,
                    password=db_password,
                    host=db_host
                )
                self.logger.success("Database connected!")
            except psycopg2.DatabaseError as err:
                self.logger.info(f"{os.getenv('db_name')}, {os.getenv('db_user')}, {os.getenv('db_password')}, {os.getenv('db_host')}")
                self.logger.error(f"An error ocurred to connect to database: {os.getenv('db_name')}: {err.pgerror}")
        return self.conn
    
    def backup_db(self):
        current_date = datetime.now().strftime("%d-%m-%Y_%H_%M_%S_%f")
        backup_dir = os.path.join(os.getcwd(), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"{current_date}.sql")
        
        pg_dump_path = "pg_dump"
        if os.name == "nt":
            import subprocess
            try:
                # Comprobar si pg_dump esta en el PATH
                subprocess.run(["pg_dump", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Buscar en rutas comunes
                import glob
                possible_paths = glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe")
                # Ordenar inversamente para intentar con la version mas reciente primero
                possible_paths.sort(reverse=True)
                if possible_paths:
                    pg_dump_path = possible_paths[0]

        os.environ["PGPASSWORD"] = str(db_password) if db_password else ""
        
        cmd = [
            pg_dump_path,
            "-U", str(db_user),
            "-h", str(db_host),
            "-p", "5432",
            "-d", str(db_name),
            "-w",
            "-f", backup_file
        ]
        
        import subprocess
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error ejecutando pg_dump con comando. STDERR: {e.stderr}")
            raise Exception(f"pg_dump falló: {e.stderr}")
        except Exception as e:
            self.logger.error(f"Error inesperado al ejecutar pg_dump: {e}")
            raise Exception(f"Falla de ejecución de pg_dump: {e}")

        AuditoriaRep().create(Auditoria({
            "Accion": "Respaldo",
            "Descripcion": "Respaldo de la base de datos",
        }))
        return backup_file
