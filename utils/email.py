# import resend
from utils.logger import Logger
from flask import render_template
from utils.config import app
from os import getenv
from flask_mail import Mail, Message
from utils.exceptions import EmailException

# Setting email sender
app.config['MAIL_SERVER'] = getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = getenv("MAIL_PORT")
app.config['MAIL_USE_TLS'] = getenv("MAIL_USE_TLS")
app.config['MAIL_USERNAME'] = getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = getenv("MAIL_USERNAME")

mail = Mail(app)
logger = Logger()

def send_email(to, subject, template, code):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.html = template
        msg.body = f"Código de verificación: {code}"
        mail.send(msg)
    except Exception as err:
        logger.error("Error al enviar el correo electrónico")
        raise EmailException("Error al enviar el correo electrónico")

