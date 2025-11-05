from flask import Flask
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder="../templates")
bcrypt: Bcrypt = Bcrypt(app)