from database.connection import Connection
from flask import Blueprint, jsonify, session, Response, request
from utils.logger import Logger
from utils.config import app
from utils.exceptions import MissingEntityData, InvalidOtpCode
import re
from os import getenv
from utils.Security import Security
from utils.validations import Validations
from utils.handler import exception_handler
from os import path
from utils.email import send_email
from flask import render_template
from datetime import datetime
import locale

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

otp_bp = Blueprint("otp", __name__)
logger = Logger()

app.secret_key = getenv("otp_secret")
app.config["SESSION_TYPE"] = "filesystem"

@otp_bp.route("/otp/send/<string:email>", methods=["GET"])
def otp(email: str):
    conn = Connection().get_connection()
    cursor = conn.cursor()
    try:
        if not email:
            raise MissingEntityData("Introduce tu correo electrónico")

        cursor.execute("SELECT \"UsuarioId\" FROM \"Usuario\" WHERE \"Email\" = %s", (email,))
        user = cursor.fetchone()

        if not user:
            raise ValueError("No se encontró un usuario con el correo electrónico proporcionado")

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Correo electrónico inválido")

        code = Security.generate_otp(6)
        email_template = render_template("otp-email.html", otp=code, date=datetime.now().strftime("%A %d/%m/%Y"))
        send_email(email, "Código de verificación", email_template, code)

        return jsonify({"otp": code}), 200
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]
    finally:
        cursor.close()

@otp_bp.route("/otp/verify/<string:code>", methods=["POST"])
def verify(code: str):
    try:
        if "otp" not in session:
            raise MissingEntityData("No se encontró un código OTP en la sesión.")
        elif not Validations.is_otp(code):
            raise InvalidOtpCode("El código OTP tiene un formato inválido")
        elif session["otp"] != code:
            raise InvalidOtpCode("El código OTP introducido no es correcto.")

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]