import base64
import resend
from utils import logger
from flask import render_template
from utils.config import app
from os import getenv
from os import path

# Setting email sender
app.config["MAIL_SERVER"] = getenv("otp_smtp")
app.config["MAIL_PORT"] = int(getenv("otp_port"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = getenv("otp_email")
app.config["MAIL_PASSWORD"] = getenv("otp_password")
app.config["RESEND_KEY"] = getenv("resend_api_key")

def send_email(to, subject, template, message):
    with app.open_resource(path.join(app.config["PUBLIC_DIR"], "logo.png"), "rb") as fp:
        base_image = base64.b64encode(fp.read()).decode("utf-8")

    html = render_template(f"{template}.html", message=message)

    params = {
        "from": f"Liceo Nacional Don Rómulo Gallegos <{app.config['MAIL_USERNAME']}>",
        "to": [to],
        "subject": subject,
        "html": html,
        "attachments": [
            {
                "filename": "logo.png",
                "content": base_image,
                "headers": {
                    "Content-ID": "<logo>",
                    "Content-Disposition": "inline"
                }
            }
        ]
    }

    resend.api_key = app.config["RESEND_KEY"]
    response = resend.Emails.send(params)
    logger.Logger().debug(response, "Email response")

    if not response:
        raise Exception("Ocurrió un error interno al intentar envíar el correo electrónico")
    
