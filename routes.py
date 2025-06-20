from flask import request, jsonify, render_template, redirect, url_for, flash
from app import app, db
from models import Healthcheck, CheckResult, AlertConfig, HealthcheckStatus
from healthcheck_engine import HealthcheckEngine
import logging

logger = logging.getLogger(__name__)


@app.route("/health")
def health():
    """Health check endpoint for Docker/Kubernetes"""
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": (
                    CheckResult.query.order_by(CheckResult.id.desc())
                    .first()
                    .timestamp.isoformat()
                    if CheckResult.query.first()
                    else None
                ),
            }
        ),
        200,
    )


@app.route("/")
def dashboard():
    """Main dashboard showing all healthchecks"""
    healthchecks = Healthcheck.query.all()
    healthcheck_data = []

    for hc in healthchecks:
        # Get the latest check result
        latest_result = (
            CheckResult.query.filter_by(healthcheck_id=hc.id)
            .order_by(CheckResult.id.desc())
            .first()
        )

        healthcheck_data.append(
            {
                "healthcheck": hc,
                "latest_result": latest_result,
                "status": latest_result.status.value if latest_result else "unknown",
            }
        )

    return render_template("dashboard.html", healthcheck_data=healthcheck_data)


# API Routes
@app.route("/api/healthchecks", methods=["GET"])
def get_healthchecks():
    """Get all healthchecks"""
    healthchecks = Healthcheck.query.all()
    return jsonify([hc.to_dict() for hc in healthchecks])


@app.route("/api/healthchecks", methods=["POST"])
def create_healthcheck():
    """Create a new healthcheck"""
    data = request.get_json()

    if not data or "name" not in data or "url" not in data:
        return jsonify({"error": "Name and URL are required"}), 400

    try:
        healthcheck = Healthcheck(
            name=data["name"],
            url=data["url"],
            expected_text=data.get("expected_text"),
            check_interval=data.get("check_interval", 300),
            timeout=data.get("timeout", 30),
            is_active=data.get("is_active", True),
        )

        db.session.add(healthcheck)
        db.session.commit()

        logger.info(f"Created healthcheck: {healthcheck.name}")
        return jsonify(healthcheck.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to create healthcheck: {str(e)}")
        return jsonify({"error": "Failed to create healthcheck"}), 500


@app.route("/api/healthchecks/<int:hc_id>", methods=["GET"])
def get_healthcheck(hc_id):
    """Get a specific healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)
    return jsonify(healthcheck.to_dict())


@app.route("/api/healthchecks/<int:hc_id>", methods=["PUT"])
def update_healthcheck(hc_id):
    """Update a healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Update fields if provided
        if "name" in data:
            healthcheck.name = data["name"]
        if "url" in data:
            healthcheck.url = data["url"]
        if "expected_text" in data:
            healthcheck.expected_text = data["expected_text"]
        if "check_interval" in data:
            healthcheck.check_interval = data["check_interval"]
        if "timeout" in data:
            healthcheck.timeout = data["timeout"]
        if "is_active" in data:
            healthcheck.is_active = data["is_active"]

        db.session.commit()
        logger.info(f"Updated healthcheck: {healthcheck.name}")
        return jsonify(healthcheck.to_dict())

    except Exception as e:
        logger.error(f"Failed to update healthcheck: {str(e)}")
        return jsonify({"error": "Failed to update healthcheck"}), 500


@app.route("/api/healthchecks/<int:hc_id>", methods=["DELETE"])
def delete_healthcheck(hc_id):
    """Delete a healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)

    try:
        db.session.delete(healthcheck)
        db.session.commit()
        logger.info(f"Deleted healthcheck: {healthcheck.name}")
        return "", 204

    except Exception as e:
        logger.error(f"Failed to delete healthcheck: {str(e)}")
        return jsonify({"error": "Failed to delete healthcheck"}), 500


@app.route("/api/healthchecks/<int:hc_id>/check", methods=["POST"])
def check_healthcheck_now(hc_id):
    """Manually trigger a healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)

    try:
        engine = HealthcheckEngine()
        result = engine.check_endpoint(healthcheck)
        logger.info(f"Manual check completed for: {healthcheck.name}")
        return jsonify(result.to_dict())

    except Exception as e:
        logger.error(f"Failed to check healthcheck: {str(e)}")
        return jsonify({"error": "Failed to perform healthcheck"}), 500


@app.route("/api/healthchecks/<int:hc_id>/results", methods=["GET"])
def get_healthcheck_results(hc_id):
    """Get check results for a healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)

    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    results = (
        CheckResult.query.filter_by(healthcheck_id=hc_id)
        .order_by(CheckResult.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "results": [result.to_dict() for result in results.items],
            "total": results.total,
            "pages": results.pages,
            "current_page": page,
        }
    )


# Alert Configuration Routes
@app.route("/api/healthchecks/<int:hc_id>/alerts", methods=["GET"])
def get_alert_configs(hc_id):
    """Get alert configurations for a healthcheck"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)
    alert_configs = AlertConfig.query.filter_by(healthcheck_id=hc_id).all()
    return jsonify([config.to_dict() for config in alert_configs])


@app.route("/api/healthchecks/<int:hc_id>/alerts", methods=["POST"])
def create_alert_config(hc_id):
    """Create an alert configuration"""
    healthcheck = Healthcheck.query.get_or_404(hc_id)
    data = request.get_json()

    if not data or "alert_type" not in data or "configuration" not in data:
        return jsonify({"error": "Alert type and configuration are required"}), 400

    try:
        alert_config = AlertConfig(
            healthcheck_id=hc_id,
            alert_type=data["alert_type"],
            configuration=data["configuration"],
            is_active=data.get("is_active", True),
        )

        db.session.add(alert_config)
        db.session.commit()

        logger.info(
            f"Created alert config for {healthcheck.name}: {data['alert_type']}"
        )
        return jsonify(alert_config.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to create alert config: {str(e)}")
        return jsonify({"error": "Failed to create alert configuration"}), 500


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert_config(alert_id):
    """Delete an alert configuration"""
    alert_config = AlertConfig.query.get_or_404(alert_id)

    try:
        db.session.delete(alert_config)
        db.session.commit()
        logger.info(f"Deleted alert config: {alert_config.id}")
        return "", 204

    except Exception as e:
        logger.error(f"Failed to delete alert config: {str(e)}")
        return jsonify({"error": "Failed to delete alert configuration"}), 500


# Status API
@app.route("/api/status", methods=["GET"])
def get_status():
    """Get overall system status"""
    total_healthchecks = Healthcheck.query.filter_by(is_active=True).count()

    # Get latest results for active healthchecks
    healthy_count = 0
    unhealthy_count = 0

    active_healthchecks = Healthcheck.query.filter_by(is_active=True).all()
    for hc in active_healthchecks:
        latest_result = (
            CheckResult.query.filter_by(healthcheck_id=hc.id)
            .order_by(CheckResult.id.desc())
            .first()
        )

        if latest_result:
            if latest_result.status == HealthcheckStatus.HEALTHY:
                healthy_count += 1
            else:
                unhealthy_count += 1

    return jsonify(
        {
            "total_healthchecks": total_healthchecks,
            "healthy": healthy_count,
            "unhealthy": unhealthy_count,
            "unknown": total_healthchecks - healthy_count - unhealthy_count,
        }
    )
