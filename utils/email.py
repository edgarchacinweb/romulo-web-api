# import resend
from utils import logger
from flask import render_template
from utils.config import app
from os import getenv
from flask_mail import Mail, Message

# Setting email sender
app.config['MAIL_SERVER'] = getenv("mail_server")
app.config['MAIL_PORT'] = getenv("mail_port")
app.config['MAIL_USE_TLS'] = getenv("mail_tls")
app.config['MAIL_USERNAME'] = getenv("mail_user")
app.config['MAIL_PASSWORD'] = getenv("mail_pwd")
app.config['MAIL_DEFAULT_SENDER'] = getenv("mail_user")

mail = Mail(app)

def send_email(to, subject, template, code):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.html = template
        msg.body = f"Código de verificación: {code}"
        mail.send(msg)
    except Exception as err:
        logger.error(err, "Error al enviar el correo")
        raise err

