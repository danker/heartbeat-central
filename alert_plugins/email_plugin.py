import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import BaseAlertPlugin

logger = logging.getLogger(__name__)


class EmailAlertPlugin(BaseAlertPlugin):
    """
    Email alert plugin using SMTP
    """

    def validate_config(self):
        required_fields = ["to_email"]
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Email plugin missing required field: {field}")

    def send_failure_alert(self, application, alert_context):
        subject = f"[ALERT] {application.name} missed heartbeat"
        message = self.format_failure_message(application, alert_context)
        self._send_email(subject, message)

    def send_recovery_alert(self, application, alert_context):
        subject = f"[RECOVERY] {application.name} heartbeat resumed"
        message = self.format_recovery_message(application, alert_context)
        self._send_email(subject, message)

    def _send_email(self, subject, message):
        try:
            # Use environment variables or config defaults
            smtp_server = self.config.get(
                "smtp_server", os.getenv("SMTP_SERVER", "smtp.gmail.com")
            )
            smtp_port = self.config.get("smtp_port", int(os.getenv("SMTP_PORT", "587")))
            username = self.config.get("username", os.getenv("SMTP_USERNAME"))
            password = self.config.get("password", os.getenv("SMTP_PASSWORD"))
            from_email = self.config.get("from_email", username)
            to_email = self.config["to_email"]

            if not username or not password:
                raise ValueError("SMTP credentials not configured")

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
