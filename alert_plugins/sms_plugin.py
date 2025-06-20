import os
import logging
from twilio.rest import Client
from .base import BaseAlertPlugin

logger = logging.getLogger(__name__)

class SMSAlertPlugin(BaseAlertPlugin):
    """
    SMS alert plugin using Twilio
    """
    
    def validate_config(self):
        required_fields = ['to_number']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"SMS plugin missing required field: {field}")
    
    def send_failure_alert(self, healthcheck, check_result):
        message = f"ALERT: {healthcheck.name} is DOWN\n{check_result.error_message or 'Unknown error'}"
        self._send_sms(message)
    
    def send_recovery_alert(self, healthcheck, check_result):
        message = f"RECOVERY: {healthcheck.name} is UP\nService has recovered successfully."
        self._send_sms(message)
    
    def _send_sms(self, message):
        try:
            # Use config or environment variables
            account_sid = self.config.get('account_sid', os.getenv('TWILIO_ACCOUNT_SID'))
            auth_token = self.config.get('auth_token', os.getenv('TWILIO_AUTH_TOKEN'))
            from_number = self.config.get('from_number', os.getenv('TWILIO_FROM_NUMBER'))
            to_number = self.config['to_number']
            
            if not account_sid or not auth_token or not from_number:
                raise ValueError("Twilio credentials not configured")
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent to {to_number}, SID: {message.sid}")
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            raise