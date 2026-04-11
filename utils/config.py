import os
from flask import Flask
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
load_dotenv()

from jinja2 import ChoiceLoader, FileSystemLoader

# Configuración de múltiples carpetas de plantillas para incluir el frontend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"))

# Agregamos la carpeta del frontend romulo-website a los cargadores de Jinja
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(base_dir, "templates")),
    FileSystemLoader(os.path.join(base_dir, "..", "romulo-website"))
])

bcrypt: Bcrypt = Bcrypt(app)
