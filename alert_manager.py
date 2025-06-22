import logging

from alert_plugins.discord_plugin import DiscordAlertPlugin
from alert_plugins.email_plugin import EmailAlertPlugin
from alert_plugins.slack_plugin import SlackAlertPlugin
from alert_plugins.sms_plugin import SMSAlertPlugin
from models import ApplicationAlertConfig

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alert plugins and sends notifications
    """

    def __init__(self):
        self.plugins = {
            "email": EmailAlertPlugin,
            "slack": SlackAlertPlugin,
            "discord": DiscordAlertPlugin,
            "sms": SMSAlertPlugin,
        }

    def send_alerts(self, application, result):
        """
        Send failure alerts for an application
        """
        alert_configs = ApplicationAlertConfig.query.filter_by(
            application_id=application.id, is_active=True
        ).all()

        for alert_config in alert_configs:
            try:
                self._send_alert(alert_config, application, result, "failure")
            except Exception as e:
                logger.error(
                    f"Failed to send {alert_config.alert_type} alert: {str(e)}"
                )

    def send_recovery_alerts(self, application, result):
        """
        Send recovery alerts for an application
        """
        alert_configs = ApplicationAlertConfig.query.filter_by(
            application_id=application.id, is_active=True
        ).all()

        for alert_config in alert_configs:
            try:
                self._send_alert(alert_config, application, result, "recovery")
            except Exception as e:
                logger.error(
                    f"Failed to send {alert_config.alert_type} recovery alert: {str(e)}"
                )

    def _send_alert(self, alert_config, application, result, alert_type):
        """
        Send a single alert using the appropriate plugin
        """
        plugin_class = self.plugins.get(alert_config.alert_type)
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

            if alert_type == "failure":
                plugin.send_failure_alert(application, alert_context)
            elif alert_type == "recovery":
                plugin.send_recovery_alert(application, alert_context)

            logger.info(f"Sent {alert_type} alert via {alert_config.alert_type}")

        except Exception as e:
            logger.error(f"Plugin {alert_config.alert_type} failed: {str(e)}")
            raise
