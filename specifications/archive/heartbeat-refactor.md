# Specification: heartbeat-refactor

## Overview
Complete paradigm shift from active endpoint monitoring to passive heartbeat monitoring. Instead of the application checking external endpoints, external applications will send heartbeats to our application. This is more efficient, scalable, and puts the responsibility of health reporting on the applications themselves.

**Current Problem:** The app actively polls external endpoints, which is inefficient and doesn't scale well.

**New Solution:** Applications register with us and send periodic heartbeats. We alert when applications miss their expected heartbeat windows.

## Requirements
### Functional Requirements
- **Application Registration**: Admin-only interface to register applications with name, expected interval, and grace period
- **UUID Generation**: Generate unique UUID for each registered application
- **Heartbeat Endpoint**: `POST /heartbeat/{uuid}` endpoint that accepts heartbeats from applications
- **Missed Heartbeat Detection**: Background job that detects when applications miss their heartbeat windows
- **Alert Integration**: Send alerts when applications miss heartbeats (using existing alert plugin system)
- **Admin Interface**: Web UI and API endpoints for managing applications
- **Heartbeat History**: Track when applications last sent heartbeats

### Non-Functional Requirements
- **Performance**: Support hundreds of applications sending heartbeats
- **Reliability**: Missed heartbeat detection should be accurate and timely
- **Configurability**: Background job frequency configurable via environment variables
- **Backward Compatibility**: None required - complete replacement of old system

## Technical Design
### Architecture
The new system replaces the active monitoring paradigm with a passive heartbeat system:

1. **Registration Phase**: Admins register applications via web UI or API
2. **Heartbeat Phase**: Applications send periodic heartbeats using their UUID
3. **Monitoring Phase**: Background job detects missed heartbeats and triggers alerts

### Components
- **Application Model**: Stores registered applications and their configurations
- **Heartbeat Endpoint**: Receives and processes incoming heartbeats
- **Heartbeat Monitor**: Background service that checks for missed heartbeats
- **Admin Interface**: Web UI for application management
- **Alert System**: Reuses existing alert plugins (email, slack, discord, sms)

### Data Model
**New Models:**
```python
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    expected_interval = db.Column(db.Integer, nullable=False)  # seconds
    grace_period = db.Column(db.Integer, default=0)  # seconds
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC))
```

**Heartbeat History (IMPLEMENTED):**
```python
class HeartbeatEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'))
    received_at = db.Column(db.DateTime, default=datetime.now(UTC))
```

**Modified Alert Model:**
- Update `AlertConfig` to reference `Application` instead of `Healthcheck`

### API Design
**Heartbeat Endpoint:**
```
POST /heartbeat/{uuid}
Response: 200 OK or 404 Not Found
```

**Admin API Endpoints:**
```
GET /api/applications - List all applications
POST /api/applications - Create new application
GET /api/applications/{id} - Get application details
PUT /api/applications/{id} - Update application
DELETE /api/applications/{id} - Delete application
```

## Implementation Details
### Files to Remove
- `healthcheck_engine.py`: Delete entirely
- `scheduler.py`: Delete entirely
- `models.py`: Remove Healthcheck, CheckResult models

### Files to Modify
- `app.py`: Remove scheduler imports and initialization
- `models.py`: Add Application model, modify AlertConfig
- `routes.py`: Replace healthcheck routes with application/heartbeat routes
- `alert_manager.py`: Update to work with Application model
- `templates/`: Update dashboard for application monitoring

### New Files
- `heartbeat_monitor.py`: Background service for detecting missed heartbeats
- `application_service.py`: Business logic for application management
- `templates/applications.html`: Admin interface for managing applications

### Dependencies
No new dependencies required - will use existing Flask, SQLAlchemy, APScheduler stack.

### Environment Variables
```
HEARTBEAT_CHECK_INTERVAL=30  # seconds between missed heartbeat checks
```

## Testing Strategy
### Unit Tests
- Application model CRUD operations
- UUID generation and validation
- Heartbeat endpoint with valid/invalid UUIDs
- Missed heartbeat detection logic
- Alert triggering conditions

### Integration Tests
- Application registration flow
- Heartbeat receiving and timestamp updates
- Background monitor detecting missed heartbeats
- Alert system integration with applications
- Admin interface workflows

### Manual Testing
1. Register a test application via web UI
2. Send heartbeats using the provided UUID
3. Stop sending heartbeats and verify alerts are triggered
4. Test grace period functionality
5. Verify admin interface shows correct application status

## Acceptance Criteria
- [x] All old healthcheck/endpoint monitoring code is removed
- [x] Admin can register applications with name, interval, and grace period
- [x] System generates UUID for each registered application
- [x] Applications can send heartbeats to `POST /heartbeat/{uuid}`
- [x] System updates last_heartbeat timestamp on successful heartbeat
- [x] Background monitor runs every configurable interval (default 30s)
- [x] Alerts are sent when applications miss heartbeat windows
- [x] Grace period is respected before sending alerts
- [x] Web UI allows viewing and managing applications
- [x] API endpoints support all application CRUD operations
- [x] Existing alert plugins (email, slack, discord, sms) work with applications
- [x] All tests pass with new system
- [x] Documentation is updated to reflect new paradigm

**SPECIFICATION COMPLETED: All acceptance criteria have been implemented and verified.**

## Open Questions
- Do we need rate limiting on the heartbeat endpoint to prevent abuse?
- Should we support bulk heartbeats (multiple UUIDs in one request) for efficiency?
- How should we handle clock skew between applications and our server?
- Should applications be able to send additional metadata with heartbeats in the future?

## References
- Current healthcheck system (to be replaced)
- Existing alert plugin architecture (to be reused)
- APScheduler documentation for background jobs
- Flask-SQLAlchemy for new models