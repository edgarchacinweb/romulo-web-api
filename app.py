from utils.config import app
from flask_cors import CORS
from flask import jsonify
from routes import *
from utils.logger import Logger
import database.connection
from apscheduler.schedulers.background import BackgroundScheduler
import os
import atexit
from utils.config import bcrypt

CORS(app)
Logger().start()

conn = database.connection.Connection()

# Config database backups
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=conn.backup_db,
    trigger="cron",
    day=1,
    hour=8,
    minute=30
)

scheduler.start()

# Turn off the scheduler at the end of the application
atexit.register(lambda: scheduler.shutdown())

# Config and create uploads folder
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
app.config["MAX_PDF_SIZE"] = 2.5 * 1024 # 2.5MB
app.config["PUBLIC_DIR"] = os.path.join(os.getcwd(), "public")

if not os.path.isdir(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Register routes
app.register_blueprint(user_bp)
app.register_blueprint(people_bp)
app.register_blueprint(otp_bp)
app.register_blueprint(registration_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(course_bp)
app.register_blueprint(student_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(calification_bp)
app.register_blueprint(report_card_bp)
app.register_blueprint(docs_bp)
app.register_blueprint(school_term_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(auditory_bp)
app.register_blueprint(class_bp)
app.register_blueprint(assistance_bp)

@app.route("/hello_world")
def hello_world():
    return jsonify({"message": "Hello World"})

pwd = bcrypt.generate_password_hash("Admin", int(os.getenv("pwd_rounds"))).decode("utf8")
Logger().debug("hash password", pwd)

# Run server
if __name__ == "__main__":
    app.run(port=os.getenv("app_port"), host="0.0.0.0", debug=os.getenv("mode") == "debug")
