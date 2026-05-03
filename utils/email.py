# import resend
from utils.logger import Logger
from flask import render_template
from utils.config import app
from os import getenv
from flask_mail import Mail, Message
from utils.exceptions import EmailException
from concurrent.futures import ThreadPoolExecutor

# Setting email sender
app.config['MAIL_SERVER'] = getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(getenv("MAIL_PORT", 587)) if getenv("MAIL_PORT") else 587
app.config['MAIL_USE_TLS'] = getenv("MAIL_USE_TLS") == "True"
app.config['MAIL_USERNAME'] = getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = getenv("MAIL_USERNAME")

mail = Mail(app)
logger = Logger()

# Crear un pool de hilos global para manejar los correos en segundo plano de forma segura en producción
email_executor = ThreadPoolExecutor(max_workers=4)

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
        
        # Enviar la tarea al pool de hilos en lugar de crear un hilo huérfano nuevo
        email_executor.submit(send_async_email, app, msg)
    except Exception as err:
        logger.error("Error al iniciar tarea de correo electrónico")
        raise EmailException("Error al enviar el correo electrónico")

