import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///healthcheck.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models import *  # noqa: F401,F403
from routes import *  # noqa: F401,F403
from scheduler import scheduler

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Schedule all existing healthchecks
        scheduler.schedule_all_healthchecks()

    try:
        app.run(debug=True)
    finally:
        scheduler.shutdown()
