import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app import app
from healthcheck_engine import HealthcheckEngine
from models import Healthcheck

logger = logging.getLogger(__name__)


class HealthcheckScheduler:
    """
    Manages scheduled healthcheck executions
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.engine = HealthcheckEngine()
        self.scheduler.start()
        logger.info("Healthcheck scheduler started")

    def schedule_all_healthchecks(self):
        """
        Schedule all active healthchecks based on their intervals
        """
        with app.app_context():
            healthchecks = Healthcheck.query.filter_by(is_active=True).all()

            # Clear existing jobs
            self.scheduler.remove_all_jobs()

            for healthcheck in healthchecks:
                self.schedule_healthcheck(healthcheck)

            logger.info(f"Scheduled {len(healthchecks)} healthchecks")

    def schedule_healthcheck(self, healthcheck):
        """
        Schedule a single healthcheck
        """
        job_id = f"healthcheck_{healthcheck.id}"

        # Remove existing job if it exists
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Add new job
        self.scheduler.add_job(
            func=self._run_healthcheck,
            trigger=IntervalTrigger(seconds=healthcheck.check_interval),
            id=job_id,
            args=[healthcheck.id],
            replace_existing=True,
        )

        logger.info(
            f"Scheduled healthcheck '{healthcheck.name}' every {healthcheck.check_interval} seconds"
        )

    def unschedule_healthcheck(self, healthcheck_id):
        """
        Remove a healthcheck from the schedule
        """
        job_id = f"healthcheck_{healthcheck_id}"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Unscheduled healthcheck {healthcheck_id}")

    def _run_healthcheck(self, healthcheck_id):
        """
        Execute a single healthcheck (called by scheduler)
        """
        with app.app_context():
            try:
                healthcheck = Healthcheck.query.get(healthcheck_id)
                if healthcheck and healthcheck.is_active:
                    self.engine.check_endpoint(healthcheck)
                else:
                    # Healthcheck was deleted or deactivated, remove from schedule
                    self.unschedule_healthcheck(healthcheck_id)

            except Exception as e:
                logger.error(f"Scheduled healthcheck {healthcheck_id} failed: {str(e)}")

    def shutdown(self):
        """
        Shutdown the scheduler
        """
        self.scheduler.shutdown()
        logger.info("Healthcheck scheduler stopped")


# Global scheduler instance
scheduler = HealthcheckScheduler()
