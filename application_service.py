import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database import db
from models import Application, HeartbeatEvent

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Business logic service for application management and heartbeat monitoring
    """

    @staticmethod
    def create_application(
        name: str, expected_interval: int, grace_period: int = 0, is_active: bool = True
    ) -> Application:
        """
        Create a new application with validation

        Args:
            name: Application name
            expected_interval: Expected heartbeat interval in seconds
            grace_period: Grace period before alerting in seconds
            is_active: Whether the application is active

        Returns:
            Created Application instance

        Raises:
            ValueError: If validation fails
        """
        # Validation
        if not name or not name.strip():
            raise ValueError("Application name cannot be empty")

        if expected_interval <= 0:
            raise ValueError("Expected interval must be positive")

        if grace_period < 0:
            raise ValueError("Grace period cannot be negative")

        # Check for duplicate names
        existing = Application.query.filter_by(name=name.strip()).first()
        if existing:
            raise ValueError(f"Application with name '{name}' already exists")

        try:
            application = Application(
                name=name.strip(),
                expected_interval=expected_interval,
                grace_period=grace_period,
                is_active=is_active,
            )

            db.session.add(application)
            db.session.commit()

            logger.info(
                f"Created application: {application.name} (UUID: {application.uuid})"
            )
            return application

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create application: {str(e)}")
            raise

    @staticmethod
    def update_application(app_id: int, **kwargs) -> Application:
        """
        Update an application with validation

        Args:
            app_id: Application ID
            **kwargs: Fields to update

        Returns:
            Updated Application instance

        Raises:
            ValueError: If validation fails
            NotFound: If application doesn't exist
        """
        application = Application.query.get(app_id)
        if not application:
            raise ValueError(f"Application with ID {app_id} not found")

        # Validation
        if "name" in kwargs:
            name = kwargs["name"]
            if not name or not name.strip():
                raise ValueError("Application name cannot be empty")

            # Check for duplicate names (excluding current app)
            existing = Application.query.filter(
                Application.name == name.strip(), Application.id != app_id
            ).first()
            if existing:
                raise ValueError(f"Application with name '{name}' already exists")

            kwargs["name"] = name.strip()

        if "expected_interval" in kwargs and kwargs["expected_interval"] <= 0:
            raise ValueError("Expected interval must be positive")

        if "grace_period" in kwargs and kwargs["grace_period"] < 0:
            raise ValueError("Grace period cannot be negative")

        try:
            # Update fields
            for key, value in kwargs.items():
                if hasattr(application, key):
                    setattr(application, key, value)

            application.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"Updated application: {application.name}")
            return application

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update application: {str(e)}")
            raise

    @staticmethod
    def get_application_status(app_id: int) -> Dict:
        """
        Get comprehensive status for an application

        Args:
            app_id: Application ID

        Returns:
            Dictionary with application status information
        """
        application = Application.query.get(app_id)
        if not application:
            raise ValueError(f"Application with ID {app_id} not found")

        # Get heartbeat statistics
        total_heartbeats = HeartbeatEvent.query.filter_by(application_id=app_id).count()

        # Get recent heartbeats (last 24 hours)
        yesterday = datetime.now() - timedelta(hours=24)
        recent_heartbeats = HeartbeatEvent.query.filter(
            HeartbeatEvent.application_id == app_id,
            HeartbeatEvent.received_at >= yesterday,
        ).count()

        # Calculate uptime percentage (basic calculation)
        uptime_percentage = ApplicationService._calculate_uptime(application)

        return {
            "application": application.to_dict(),
            "is_overdue": application.is_overdue(),
            "total_heartbeats": total_heartbeats,
            "recent_heartbeats_24h": recent_heartbeats,
            "uptime_percentage": uptime_percentage,
            "next_expected_heartbeat": ApplicationService._get_next_expected_heartbeat(
                application
            ),
        }

    @staticmethod
    def get_overdue_applications() -> List[Application]:
        """
        Get all applications that are currently overdue for heartbeats

        Returns:
            List of overdue Application instances
        """
        active_applications = Application.query.filter_by(is_active=True).all()
        return [app for app in active_applications if app.is_overdue()]

    @staticmethod
    def get_system_statistics() -> Dict:
        """
        Get overall system statistics for heartbeat monitoring

        Returns:
            Dictionary with system-wide statistics
        """
        total_applications = Application.query.count()
        active_applications = Application.query.filter_by(is_active=True).count()
        overdue_applications = ApplicationService.get_overdue_applications()

        # Get heartbeat counts
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        heartbeats_today = HeartbeatEvent.query.filter(
            HeartbeatEvent.received_at >= today
        ).count()

        return {
            "total_applications": total_applications,
            "active_applications": active_applications,
            "overdue_applications": len(overdue_applications),
            "healthy_applications": active_applications - len(overdue_applications),
            "heartbeats_today": heartbeats_today,
            "overdue_app_names": [app.name for app in overdue_applications],
        }

    @staticmethod
    def cleanup_old_heartbeat_events(days_to_keep: int = 30) -> int:
        """
        Clean up old heartbeat events to prevent database bloat

        Args:
            days_to_keep: Number of days of heartbeat events to keep

        Returns:
            Number of events deleted
        """
        if days_to_keep <= 0:
            raise ValueError("Days to keep must be positive")

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            deleted_count = HeartbeatEvent.query.filter(
                HeartbeatEvent.received_at < cutoff_date
            ).delete()

            db.session.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old heartbeat events")

            return deleted_count

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old heartbeat events: {str(e)}")
            raise

    @staticmethod
    def _calculate_uptime(application: Application) -> float:
        """
        Calculate basic uptime percentage for an application

        This is a simplified calculation based on expected vs actual heartbeats
        in the last 24 hours.

        Args:
            application: Application instance

        Returns:
            Uptime percentage (0.0 to 100.0)
        """
        if not application.last_heartbeat:
            return 0.0

        # Calculate expected heartbeats in the last 24 hours
        hours_24 = 24 * 3600  # 24 hours in seconds
        expected_heartbeats = hours_24 // application.expected_interval

        # Get actual heartbeats in the last 24 hours
        yesterday = datetime.now() - timedelta(hours=24)
        actual_heartbeats = HeartbeatEvent.query.filter(
            HeartbeatEvent.application_id == application.id,
            HeartbeatEvent.received_at >= yesterday,
        ).count()

        if expected_heartbeats == 0:
            return 100.0

        uptime = min(100.0, (actual_heartbeats / expected_heartbeats) * 100.0)
        return round(uptime, 2)

    @staticmethod
    def _get_next_expected_heartbeat(application: Application) -> Optional[str]:
        """
        Calculate when the next heartbeat is expected

        Args:
            application: Application instance

        Returns:
            ISO formatted datetime string or None if never received a heartbeat
        """
        if not application.last_heartbeat:
            return None

        next_expected = application.last_heartbeat + timedelta(
            seconds=application.expected_interval
        )

        return next_expected.isoformat()

    @staticmethod
    def simulate_heartbeat(app_uuid: str) -> bool:
        """
        Simulate a heartbeat for testing purposes

        Args:
            app_uuid: Application UUID

        Returns:
            True if successful, False if application not found
        """
        application = Application.query.filter_by(uuid=app_uuid).first()
        if not application:
            return False

        try:
            # Update last heartbeat
            application.last_heartbeat = datetime.now()

            # Create heartbeat event
            heartbeat_event = HeartbeatEvent(
                application_id=application.id, received_at=datetime.now()
            )

            db.session.add(heartbeat_event)
            db.session.commit()

            logger.info(f"Simulated heartbeat for {application.name}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to simulate heartbeat: {str(e)}")
            return False
