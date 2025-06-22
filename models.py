import uuid
from datetime import datetime, timedelta

from database import db


class Application(db.Model):
    """
    Model for applications that send heartbeats to us
    """

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(100), nullable=False)
    expected_interval = db.Column(db.Integer, nullable=False)  # seconds
    grace_period = db.Column(db.Integer, default=0)  # seconds
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    heartbeat_events = db.relationship(
        "HeartbeatEvent", backref="application", lazy=True, cascade="all, delete-orphan"
    )
    alert_configs = db.relationship(
        "ApplicationAlertConfig",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Application {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "expected_interval": self.expected_interval,
            "grace_period": self.grace_period,
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_overdue(self):
        """
        Check if this application is overdue for a heartbeat
        """
        if not self.last_heartbeat:
            # Never received heartbeat, overdue if created > interval + grace ago
            threshold = datetime.now() - timedelta(
                seconds=self.expected_interval + self.grace_period
            )
            return self.created_at <= threshold

        # Check if last heartbeat is older than expected interval + grace period
        threshold = datetime.now() - timedelta(
            seconds=self.expected_interval + self.grace_period
        )
        return self.last_heartbeat <= threshold


class HeartbeatEvent(db.Model):
    """
    Optional model for logging heartbeat events (for history/analytics)
    """

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("application.id"), nullable=False
    )
    received_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<HeartbeatEvent {self.application_id}: {self.received_at}>"

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }


class ApplicationAlertConfig(db.Model):
    """
    Alert configurations for applications (separate from healthcheck alerts)
    """

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("application.id"), nullable=False
    )
    alert_type = db.Column(db.String(50), nullable=False)  # email, slack, discord, sms
    configuration = db.Column(db.JSON, nullable=False)  # stores plugin-specific config
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ApplicationAlertConfig {self.application_id}: {self.alert_type}>"

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "alert_type": self.alert_type,
            "configuration": self.configuration,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
