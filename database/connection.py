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
        backup_file = os.path.join(os.getcwd(), "backups", f"{current_date}.sql")
        os.system(f"pg_dump postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name} -f {backup_file}");
        AuditoriaRep().create(Auditoria({
            "Accion": "Respaldo",
            "Descripcion": "Respaldo de la base de datos",
        }))
        return backup_file
