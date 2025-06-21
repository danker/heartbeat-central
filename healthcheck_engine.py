import logging
import time
from datetime import datetime

import requests

from alert_manager import AlertManager
from database import db
from models import CheckResult, Healthcheck, HealthcheckStatus

logger = logging.getLogger(__name__)


class HealthcheckEngine:
    def __init__(self):
        self.alert_manager = AlertManager()

    def check_endpoint(self, healthcheck):
        """
        Perform a healthcheck on a single endpoint
        """
        logger.info(f"Checking endpoint: {healthcheck.name} ({healthcheck.url})")

        start_time = time.time()
        result = CheckResult(healthcheck_id=healthcheck.id)

        try:
            response = requests.get(
                healthcheck.url,
                timeout=healthcheck.timeout,
                headers={"User-Agent": "HealthcheckApp/1.0"},
            )

            response_time = time.time() - start_time
            result.response_time = response_time
            result.status_code = response.status_code

            # Check if response is successful
            if response.status_code >= 200 and response.status_code < 300:
                # Check for expected text if specified
                if healthcheck.expected_text:
                    if healthcheck.expected_text.lower() in response.text.lower():
                        result.status = HealthcheckStatus.HEALTHY
                        logger.info(
                            f"✓ {healthcheck.name}: Healthy (found expected text)"
                        )
                    else:
                        result.status = HealthcheckStatus.UNHEALTHY
                        expected_text = healthcheck.expected_text
                        result.error_message = (
                            f"Expected text '{expected_text}' not found in response"
                        )
                        logger.warning(
                            f"✗ {healthcheck.name}: Unhealthy (expected text not found)"
                        )
                else:
                    result.status = HealthcheckStatus.HEALTHY
                    logger.info(
                        f"✓ {healthcheck.name}: Healthy (HTTP {response.status_code})"
                    )
            else:
                result.status = HealthcheckStatus.UNHEALTHY
                result.error_message = f"HTTP {response.status_code}: {response.reason}"
                logger.warning(
                    f"✗ {healthcheck.name}: Unhealthy (HTTP {response.status_code})"
                )

        except requests.exceptions.Timeout:
            result.status = HealthcheckStatus.UNHEALTHY
            result.error_message = (
                f"Request timeout after {healthcheck.timeout} seconds"
            )
            logger.error(f"✗ {healthcheck.name}: Timeout")

        except requests.exceptions.ConnectionError as e:
            result.status = HealthcheckStatus.UNHEALTHY
            result.error_message = f"Connection error: {str(e)}"
            logger.error(f"✗ {healthcheck.name}: Connection error")

        except Exception as e:
            result.status = HealthcheckStatus.UNHEALTHY
            result.error_message = f"Unexpected error: {str(e)}"
            logger.error(f"✗ {healthcheck.name}: Unexpected error - {str(e)}")

        # Save result to database
        result.checked_at = datetime.now(datetime.UTC)
        db.session.add(result)
        db.session.commit()

        # Check if we need to send alerts
        self._check_and_send_alerts(healthcheck, result)

        return result

    def _check_and_send_alerts(self, healthcheck, current_result):
        """
        Check if we need to send alerts based on the current result
        """
        if current_result.status == HealthcheckStatus.UNHEALTHY:
            # Get the last result to see if this is a new failure
            last_result = (
                CheckResult.query.filter_by(healthcheck_id=healthcheck.id)
                .order_by(CheckResult.id.desc())
                .offset(1)
                .first()
            )

            # Send alert if this is a new failure or if the last check was healthy
            if not last_result or last_result.status == HealthcheckStatus.HEALTHY:
                logger.info(f"Sending failure alert for {healthcheck.name}")
                self.alert_manager.send_alerts(healthcheck, current_result)

        elif current_result.status == HealthcheckStatus.HEALTHY:
            # Get the last result to see if this is a recovery
            last_result = (
                CheckResult.query.filter_by(healthcheck_id=healthcheck.id)
                .order_by(CheckResult.id.desc())
                .offset(1)
                .first()
            )

            # Send recovery alert if the last check was unhealthy
            if last_result and last_result.status == HealthcheckStatus.UNHEALTHY:
                logger.info(f"Sending recovery alert for {healthcheck.name}")
                self.alert_manager.send_recovery_alerts(healthcheck, current_result)

    def check_all_active_endpoints(self):
        """
        Check all active healthcheck endpoints
        """
        active_healthchecks = Healthcheck.query.filter_by(is_active=True).all()

        logger.info(f"Checking {len(active_healthchecks)} active endpoints")

        results = []
        for healthcheck in active_healthchecks:
            try:
                result = self.check_endpoint(healthcheck)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to check {healthcheck.name}: {str(e)}")

        return results
