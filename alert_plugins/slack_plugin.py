import requests
import logging
from .base import BaseAlertPlugin

logger = logging.getLogger(__name__)

class SlackAlertPlugin(BaseAlertPlugin):
    """
    Slack alert plugin using webhooks
    """
    
    def validate_config(self):
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Slack plugin missing required field: {field}")
    
    def send_failure_alert(self, healthcheck, check_result):
        message = self.format_failure_message(healthcheck, check_result)
        self._send_slack_message(message, color='danger')
    
    def send_recovery_alert(self, healthcheck, check_result):
        message = self.format_recovery_message(healthcheck, check_result)
        self._send_slack_message(message, color='good')
    
    def _send_slack_message(self, message, color='warning'):
        try:
            webhook_url = self.config['webhook_url']
            channel = self.config.get('channel')
            username = self.config.get('username', 'HealthcheckBot')
            
            payload = {
                'username': username,
                'attachments': [{
                    'color': color,
                    'text': message,
                    'mrkdwn_in': ['text']
                }]
            }
            
            if channel:
                payload['channel'] = channel
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack message sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            raise