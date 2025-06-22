import logging
import os

from dotenv import load_dotenv
from flask import Flask

from database import db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///healthcheck.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from heartbeat_monitor import HeartbeatMonitor  # noqa: E402
from models import *  # noqa: F401,F403,E402
from routes import *  # noqa: F401,F403,E402

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # Initialize and start heartbeat monitor
    heartbeat_monitor = HeartbeatMonitor(app)
    heartbeat_monitor.start()

    try:
        debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        port = int(os.getenv("PORT", "5000"))
        logger.info("Starting Flask application with heartbeat monitoring enabled")
        app.run(host="0.0.0.0", port=port, debug=debug_mode)
    finally:
        heartbeat_monitor.stop()
