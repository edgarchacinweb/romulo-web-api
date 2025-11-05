from models.Usuario import Usuario
from utils.helpers import date_to_str, str_to_date
from datetime import date

class Auditoria():
    def __init__(self, *args):
        self.id: str = None
        self.usuario: Usuario = None
        self.descripcion: str = None
        self.accion: str = None
        self.fecha: date = None
        
        if len(args) > 1:
            self.id = args[0]
            self.usuario = args[1]
            self.descripcion = args[2]
            self.accion = args[3]
            self.fecha = args[4]
        elif len(args) == 1 and isinstance(args[0], dict):
            auditory_dict = args[0]
            if "id" in auditory_dict: self.id = auditory_dict["id"]
            if "Usuario" in auditory_dict: self.usuario = auditory_dict["Usuario"]
            if "Descripcion" in auditory_dict: self.descripcion = auditory_dict["Descripcion"]
            if "Accion" in auditory_dict: self.accion = auditory_dict["Accion"]
            if "Fecha" in auditory_dict: self.fecha = str_to_date(auditory_dict["Fecha"])
            if "UsuarioId" in auditory_dict: self.usuario.id = auditory_dict["UsuarioId"]
        else:
            auditory_tuple = args[0]
            self.id = auditory_tuple[0]
            self.usuario = auditory_tuple[1]
            self.descripcion = auditory_tuple[2]
            self.accion = auditory_tuple[3]
            self.fecha = auditory_tuple[4]

    def to_dict(self):
        auditory = dict()
        if self.id: auditory["AuditoriaId"] = self.id
        if self.usuario: auditory["Usuario"] = self.usuario.to_dict()
        if self.descripcion: auditory["Descripcion"] = self.descripcion
        if self.accion: auditory["Accion"] = self.accion
        if self.fecha: auditory["Fecha"] = date_to_str(self.fecha)
        return auditory

    def to_tuple(self):
        return (self.usuario.id, self.descripcion, self.accion)

