import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAlertPlugin(ABC):
    """
    Base class for all alert plugins
    """

    def __init__(self, config):
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self):
        """
        Validate the plugin configuration
        Raise ValueError if configuration is invalid
        """
        pass

    @abstractmethod
    def send_failure_alert(self, application, alert_context):
        """
        Send an alert when an application misses its heartbeat

        Args:
            application: Application model instance
            alert_context: Dictionary containing alert information
        """
        pass

    @abstractmethod
    def send_recovery_alert(self, application, alert_context):
        """
        Send an alert when an application recovers (resumes heartbeats)

        Args:
            application: Application model instance
            alert_context: Dictionary containing alert information
        """
        pass

    def format_failure_message(self, application, alert_context):
        """
        Format a failure alert message
        """
        last_seen = alert_context.get("last_seen_at", "Never")
        if last_seen != "Never":
            last_seen = last_seen.strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""
🚨 HEARTBEAT MISSED

Application: {application.name}
UUID: {application.uuid}
Expected Interval: {application.expected_interval}s
Grace Period: {application.grace_period}s
Last Heartbeat: {last_seen}
Time: {alert_context.get('checked_at', 'Unknown').strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()

    def format_recovery_message(self, application, alert_context):
        """
        Format a recovery alert message
        """
        return f"""
✅ HEARTBEAT RECOVERED

Application: {application.name}
UUID: {application.uuid}
Expected Interval: {application.expected_interval}s
Time: {alert_context.get('recovered_at', 'Unknown').strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
