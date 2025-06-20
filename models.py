from app import db
from datetime import datetime
from enum import Enum


class HealthcheckStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Healthcheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    expected_text = db.Column(db.String(500), nullable=True)
    check_interval = db.Column(db.Integer, default=300)  # seconds
    timeout = db.Column(db.Integer, default=30)  # seconds
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    check_results = db.relationship(
        "CheckResult", backref="healthcheck", lazy=True, cascade="all, delete-orphan"
    )
    alert_configs = db.relationship(
        "AlertConfig", backref="healthcheck", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Healthcheck {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "expected_text": self.expected_text,
            "check_interval": self.check_interval,
            "timeout": self.timeout,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CheckResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    healthcheck_id = db.Column(
        db.Integer, db.ForeignKey("healthcheck.id"), nullable=False
    )
    status = db.Column(db.Enum(HealthcheckStatus), nullable=False)
    response_time = db.Column(db.Float)  # in seconds
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CheckResult {self.healthcheck_id}: {self.status.value}>"

    def to_dict(self):
        return {
            "id": self.id,
            "healthcheck_id": self.healthcheck_id,
            "status": self.status.value,
            "response_time": self.response_time,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }


class AlertConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    healthcheck_id = db.Column(
        db.Integer, db.ForeignKey("healthcheck.id"), nullable=False
    )
    alert_type = db.Column(db.String(50), nullable=False)  # email, slack, discord, sms
    configuration = db.Column(db.JSON, nullable=False)  # stores plugin-specific config
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AlertConfig {self.healthcheck_id}: {self.alert_type}>"

    def to_dict(self):
        return {
            "id": self.id,
            "healthcheck_id": self.healthcheck_id,
            "alert_type": self.alert_type,
            "configuration": self.configuration,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
