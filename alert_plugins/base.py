from abc import ABC, abstractmethod
import logging

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
    def send_failure_alert(self, healthcheck, check_result):
        """
        Send an alert when a healthcheck fails
        
        Args:
            healthcheck: Healthcheck model instance
            check_result: CheckResult model instance
        """
        pass
    
    @abstractmethod
    def send_recovery_alert(self, healthcheck, check_result):
        """
        Send an alert when a healthcheck recovers
        
        Args:
            healthcheck: Healthcheck model instance
            check_result: CheckResult model instance
        """
        pass
    
    def format_failure_message(self, healthcheck, check_result):
        """
        Format a failure alert message
        """
        return f"""
🚨 HEALTHCHECK FAILURE

Service: {healthcheck.name}
URL: {healthcheck.url}
Status: {check_result.status.value.upper()}
Error: {check_result.error_message or 'Unknown error'}
Response Time: {check_result.response_time:.2f}s if check_result.response_time else 'N/A'
Status Code: {check_result.status_code or 'N/A'}
Time: {check_result.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
    
    def format_recovery_message(self, healthcheck, check_result):
        """
        Format a recovery alert message
        """
        return f"""
✅ HEALTHCHECK RECOVERED

Service: {healthcheck.name}
URL: {healthcheck.url}
Status: {check_result.status.value.upper()}
Response Time: {check_result.response_time:.2f}s if check_result.response_time else 'N/A'
Status Code: {check_result.status_code or 'N/A'}
Time: {check_result.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()