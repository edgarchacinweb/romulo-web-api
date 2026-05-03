from utils.config import app
from flask_mail import Mail, Message
from os import getenv
from dotenv import load_dotenv
load_dotenv()

app.config['MAIL_SERVER'] = getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = getenv("MAIL_USE_TLS") == "True"
app.config['MAIL_USERNAME'] = getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = getenv("MAIL_USERNAME")

mail = Mail(app)

def test_sync():
    with app.app_context():
        msg = Message("Test Subject", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
        msg.body = "Test body"
        msg.html = "<p>Test body</p>"
        try:
            print("Sending email...")
            mail.send(msg)
            print("Sync send success!")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("Sync send failed:", str(e))

if __name__ == "__main__":
    test_sync()
