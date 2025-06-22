import logging
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from alert_manager import AlertManager
from models import Application, ApplicationAlertConfig

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """
    Background service that monitors applications for missed heartbeats
    and triggers alerts when applications are overdue.
    """

    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.alert_manager = AlertManager()
        self.app = app
        self.check_interval = int(os.getenv("HEARTBEAT_CHECK_INTERVAL", 30))  # seconds
        self._overdue_applications = set()  # Track which apps are currently overdue

    def start(self):
        """Start the heartbeat monitoring service"""
        if self.scheduler.running:
            logger.warning("Heartbeat monitor is already running")
            return

        # Schedule the heartbeat check job
        self.scheduler.add_job(
            func=self._check_heartbeats,
            trigger=IntervalTrigger(seconds=self.check_interval),
            id="heartbeat_monitor",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Heartbeat monitor started - checking every {self.check_interval} seconds"
        )

    def stop(self):
        """Stop the heartbeat monitoring service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Heartbeat monitor stopped")

    def _check_heartbeats(self):
        """
        Check all active applications for missed heartbeats
        This method is called by the scheduler at regular intervals
        """
        if not self.app:
            logger.error("No Flask app context available for heartbeat monitoring")
            return

        with self.app.app_context():
            try:
                # Get all active applications
                active_applications = Application.query.filter_by(is_active=True).all()

                logger.debug(f"Checking {len(active_applications)} active applications")

                for application in active_applications:
                    self._check_application_heartbeat(application)

            except Exception as e:
                logger.error(f"Error during heartbeat check: {str(e)}")

    def _check_application_heartbeat(self, application):
        """
        Check a single application for missed heartbeats and handle alerts
        """
        try:
            is_currently_overdue = application.is_overdue()
            was_previously_overdue = application.id in self._overdue_applications

            if is_currently_overdue and not was_previously_overdue:
                # Application just became overdue - send alert
                self._send_missed_heartbeat_alert(application)
                self._overdue_applications.add(application.id)
                logger.warning(f"Application '{application.name}' is now overdue")

            elif not is_currently_overdue and was_previously_overdue:
                # Application recovered - send recovery alert
                self._send_heartbeat_recovery_alert(application)
                self._overdue_applications.discard(application.id)
                logger.info(f"Application '{application.name}' has recovered")

            elif is_currently_overdue and was_previously_overdue:
                # Still overdue - optionally could send reminder alerts here
                logger.debug(f"Application '{application.name}' remains overdue")

        except Exception as e:
            logger.error(f"Error checking heartbeat for {application.name}: {str(e)}")

    def _send_missed_heartbeat_alert(self, application):
        """
        Send alerts when an application misses its heartbeat window
        """
        try:
            alert_configs = ApplicationAlertConfig.query.filter_by(
                application_id=application.id, is_active=True
            ).all()

            if not alert_configs:
                logger.warning(
                    f"No active alert configs for application {application.name}"
                )
                return

            # Create a mock "check result" for compatibility with existing alert system
            mock_result = {
                "status": "missed_heartbeat",
                "application": application.name,
                "last_heartbeat": application.last_heartbeat,
                "expected_interval": application.expected_interval,
                "grace_period": application.grace_period,
                "checked_at": datetime.now(),
            }

            for alert_config in alert_configs:
                try:
                    self._send_application_alert(
                        alert_config, application, mock_result, "missed_heartbeat"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send {alert_config.alert_type} alert: {str(e)}"
                    )

            logger.info(f"Sent missed heartbeat alerts for {application.name}")

        except Exception as e:
            logger.error(f"Error sending missed heartbeat alert: {str(e)}")

    def _send_heartbeat_recovery_alert(self, application):
        """
        Send recovery alerts when an application starts sending heartbeats again
        """
        try:
            alert_configs = ApplicationAlertConfig.query.filter_by(
                application_id=application.id, is_active=True
            ).all()

            # Create a mock "check result" for recovery
            mock_result = {
                "status": "heartbeat_recovered",
                "application": application.name,
                "last_heartbeat": application.last_heartbeat,
                "checked_at": datetime.now(),
            }

            for alert_config in alert_configs:
                try:
                    self._send_application_alert(
                        alert_config, application, mock_result, "recovery"
                    )
                except Exception as e:
                    logger.error(f"Failed to send recovery alert: {str(e)}")

            logger.info(f"Sent heartbeat recovery alerts for {application.name}")

        except Exception as e:
            logger.error(f"Error sending heartbeat recovery alert: {str(e)}")

    def _send_application_alert(self, alert_config, application, result, alert_type):
        """
        Send a single alert using the alert manager
        """
        plugin_class = self.alert_manager.plugins.get(alert_config.alert_type)
        if not plugin_class:
            logger.error(f"Unknown alert type: {alert_config.alert_type}")
            return

        try:
            plugin = plugin_class(alert_config.configuration)

            # Create alert context from result
            alert_context = (
                result
                if isinstance(result, dict)
                else {
                    "checked_at": result,
                    "last_seen_at": getattr(application, "last_heartbeat_at", None),
                    "recovered_at": result if alert_type == "recovery" else None,
                }
            )

            if alert_type == "missed_heartbeat":
                plugin.send_failure_alert(application, alert_context)
            elif alert_type == "recovery":
                plugin.send_recovery_alert(application, alert_context)

            logger.info(f"Sent {alert_type} alert via {alert_config.alert_type}")

        except Exception as e:
            logger.error(f"Alert plugin {alert_config.alert_type} failed: {str(e)}")
            raise

    def get_status(self):
        """
        Get the current status of the heartbeat monitor
        """
        return {
            "running": self.scheduler.running,
            "check_interval": self.check_interval,
            "overdue_applications": len(self._overdue_applications),
            "overdue_app_ids": list(self._overdue_applications),
        }
