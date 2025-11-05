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

otp_bp = Blueprint("otp", __name__)
logger = Logger()

app.secret_key = getenv("otp_secret")
app.config["SESSION_TYPE"] = "filesystem"

@otp_bp.route("/otp/send", methods=["POST"])
def otp():
    try:
        data = request.get_json()

        if not data or "Email" not in data:
            raise MissingEntityData("Introduce tu correo electrónico")

        email = data["Email"]

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Correo electrónico inválido")

        code = Security.generate_otp(6)
        session["otp"] = code

        send_email(email, "Código de verificación", "otp-email", code)

        return Response(status=200)
    except Exception as err:
        ex = exception_handler(err)
        return jsonify(ex[0]), ex[1]

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