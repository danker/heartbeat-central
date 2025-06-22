import logging

import requests

from .base import BaseAlertPlugin

logger = logging.getLogger(__name__)


class DiscordAlertPlugin(BaseAlertPlugin):
    """
    Discord alert plugin using webhooks
    """

    def validate_config(self):
        required_fields = ["webhook_url"]
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Discord plugin missing required field: {field}")

    def send_failure_alert(self, application, alert_context):
        message = self.format_failure_message(application, alert_context)
        self._send_discord_message(message, color=0xFF0000)  # Red

    def send_recovery_alert(self, application, alert_context):
        message = self.format_recovery_message(application, alert_context)
        self._send_discord_message(message, color=0x00FF00)  # Green

    def _send_discord_message(self, message, color=0xFFAA00):
        try:
            webhook_url = self.config["webhook_url"]
            username = self.config.get("username", "HeartbeatBot")

            payload = {
                "username": username,
                "embeds": [{"description": message, "color": color}],
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("Discord message sent successfully")

        except Exception as e:
            logger.error(f"Failed to send Discord message: {str(e)}")
            raise
