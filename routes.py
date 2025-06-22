import logging
from datetime import datetime

from flask import jsonify, render_template, request

from app import app
from database import db
from models import (
    Application,
    HeartbeatEvent,
)

logger = logging.getLogger(__name__)


@app.route("/health")
def health():
    """Health check endpoint for Docker/Kubernetes"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200


@app.route("/heartbeat/<uuid:app_uuid>", methods=["POST"])
def receive_heartbeat(app_uuid):
    """
    Receive heartbeat from an application

    Applications send POST requests to this endpoint with their UUID
    to indicate they are alive and functioning.
    """
    try:
        # Convert UUID to string for database lookup
        app_uuid_str = str(app_uuid)

        # Find the application by UUID
        application = Application.query.filter_by(uuid=app_uuid_str).first()

        if not application:
            logger.warning(
                f"Heartbeat received for unknown application: {app_uuid_str}"
            )
            return jsonify({"error": "Application not found"}), 404

        if not application.is_active:
            logger.warning(
                f"Heartbeat received for inactive application: {application.name}"
            )
            return jsonify({"error": "Application is not active"}), 400

        # Update last heartbeat timestamp
        application.last_heartbeat = datetime.now()

        # Optional: Log the heartbeat event for history/analytics
        heartbeat_event = HeartbeatEvent(
            application_id=application.id, received_at=datetime.now()
        )

        db.session.add(heartbeat_event)
        db.session.commit()

        logger.info(f"Heartbeat received from {application.name} ({app_uuid_str})")

        return (
            jsonify(
                {
                    "status": "ok",
                    "application": application.name,
                    "timestamp": application.last_heartbeat.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error processing heartbeat for {app_uuid}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


@app.route("/")
def dashboard():
    """Main dashboard showing all applications"""
    applications = Application.query.all()
    application_data = []

    for application in applications:
        # Get the latest heartbeat
        latest_heartbeat = (
            HeartbeatEvent.query.filter_by(application_id=application.id)
            .order_by(HeartbeatEvent.id.desc())
            .first()
        )

        # Determine status
        if application.is_overdue():
            status = "overdue"
        elif application.last_heartbeat:
            status = "healthy"
        else:
            status = "unknown"

        application_data.append(
            {
                "application": application,
                "latest_heartbeat": latest_heartbeat,
                "status": status,
                "is_overdue": application.is_overdue(),
            }
        )

    return render_template("dashboard.html", application_data=application_data)


# Application Management API Routes
@app.route("/api/applications", methods=["GET"])
def get_applications():
    """Get all applications"""
    applications = Application.query.all()
    return jsonify([app.to_dict() for app in applications])


@app.route("/api/applications", methods=["POST"])
def create_application():
    """Create a new application for heartbeat monitoring"""
    data = request.get_json()

    if not data or "name" not in data or "expected_interval" not in data:
        return jsonify({"error": "Name and expected_interval are required"}), 400

    try:
        application = Application(
            name=data["name"],
            expected_interval=data["expected_interval"],
            grace_period=data.get("grace_period", 0),
            is_active=data.get("is_active", True),
        )

        db.session.add(application)
        db.session.commit()

        logger.info(
            f"Created application: {application.name} (UUID: {application.uuid})"
        )
        return jsonify(application.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to create application: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to create application"}), 500


@app.route("/api/applications/<int:app_id>", methods=["GET"])
def get_application(app_id):
    """Get a specific application"""
    application = Application.query.get_or_404(app_id)

    # Include additional status information
    app_data = application.to_dict()
    app_data["is_overdue"] = application.is_overdue()

    # Get recent heartbeat events
    recent_events = (
        HeartbeatEvent.query.filter_by(application_id=app_id)
        .order_by(HeartbeatEvent.id.desc())
        .limit(10)
        .all()
    )
    app_data["recent_heartbeats"] = [event.to_dict() for event in recent_events]

    return jsonify(app_data)


@app.route("/api/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id):
    """Update an application"""
    application = Application.query.get_or_404(app_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Update fields if provided
        if "name" in data:
            application.name = data["name"]
        if "expected_interval" in data:
            application.expected_interval = data["expected_interval"]
        if "grace_period" in data:
            application.grace_period = data["grace_period"]
        if "is_active" in data:
            application.is_active = data["is_active"]

        application.updated_at = datetime.now()
        db.session.commit()

        logger.info(f"Updated application: {application.name}")
        return jsonify(application.to_dict())

    except Exception as e:
        logger.error(f"Failed to update application: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update application"}), 500


@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
def delete_application(app_id):
    """Delete an application"""
    application = Application.query.get_or_404(app_id)

    try:
        db.session.delete(application)
        db.session.commit()

        logger.info(
            f"Deleted application: {application.name} (UUID: {application.uuid})"
        )
        return "", 204

    except Exception as e:
        logger.error(f"Failed to delete application: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete application"}), 500


@app.route("/api/applications/<int:app_id>/heartbeats", methods=["GET"])
def get_application_heartbeats(app_id):
    """Get heartbeat history for an application"""
    Application.query.get_or_404(app_id)  # Verify application exists

    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    heartbeats = (
        HeartbeatEvent.query.filter_by(application_id=app_id)
        .order_by(HeartbeatEvent.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "heartbeats": [heartbeat.to_dict() for heartbeat in heartbeats.items],
            "total": heartbeats.total,
            "pages": heartbeats.pages,
            "current_page": page,
        }
    )
