# import resend
from utils.logger import Logger
from flask import render_template
from utils.config import app
from os import getenv
from flask_mail import Mail, Message
from utils.exceptions import EmailException
from threading import Thread

# Setting email sender
app.config['MAIL_SERVER'] = getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = getenv("MAIL_PORT")
app.config['MAIL_USE_TLS'] = getenv("MAIL_USE_TLS")
app.config['MAIL_USERNAME'] = getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = getenv("MAIL_USERNAME")

mail = Mail(app)
logger = Logger()

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as err:
            logger.error(f"Error asincrono enviando correo: {str(err)}")

def send_email(to, subject, template, body):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.html = template
        msg.body = body
        thread = Thread(target=send_async_email, args=(app, msg))
        thread.start()
    except Exception as err:
        logger.error("Error al iniciar thread de correo electrónico")
        raise EmailException("Error al enviar el correo electrónico")

