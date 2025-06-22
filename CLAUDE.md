# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Heartbeat Central is a Flask-based centralized heartbeat monitoring service with pluggable alerting system. Applications register with the service and send periodic heartbeats. The system alerts when applications miss their expected heartbeat windows.

## Development Commands

### Setup
```bash
# Using uv (recommended)
uv pip install -e ".[dev]"
cp .env.example .env

# Or using pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

### Running the Application
```bash
python app.py
# Access at http://localhost:5000
```

### Testing
```bash
# Using script
./scripts/test.sh

# Or directly
uv run pytest -v

# Run specific test
uv run pytest tests/test_basic.py::test_health_endpoint -v
```

### Code Quality
```bash
# Using script (runs isort, black, flake8)
./scripts/lint.sh

# Or individually
uv run black .
uv run flake8 .
uv run isort .
```

## High-Level Architecture

### Core Components
1. **Flask Application** (`app.py`): Entry point that initializes the web server and background monitor
2. **Heartbeat Monitor** (`heartbeat_monitor.py`): APScheduler-based service that runs every 30 seconds to check for overdue applications
3. **Alert Manager** (`alert_manager.py`): Plugin system that loads and manages alert channels (email, Slack, Discord, SMS)
4. **Routes** (`routes.py`): All API endpoints and web UI routes
5. **Models** (`models.py`): SQLAlchemy models for Application, HeartbeatEvent, and ApplicationAlertConfig

### Data Flow
```
Application Registration → Creates Application record with UUID
                          ↓
Heartbeat Reception → POST /heartbeat/{uuid}
                     → Updates last_heartbeat timestamp
                     → Creates HeartbeatEvent record
                     ↓
Background Monitor → Queries for overdue applications
                    (current_time > last_heartbeat + interval + grace_period)
                    ↓
Alert Triggering → Loads ApplicationAlertConfig
                  → Sends via configured alert plugins
```

### Database Schema
- **Application**: Stores app metadata, heartbeat interval, grace period
- **HeartbeatEvent**: History of all received heartbeats
- **ApplicationAlertConfig**: JSON configuration for each alert type per application

### Alert Plugin Architecture
Alert plugins are loaded dynamically from `alert_plugins/` directory. Each plugin must:
- Inherit from `BaseAlertPlugin`
- Implement `send_alert(application, message, config)` method
- Define `CONFIG_SCHEMA` for validation

## Specification Workflow

Before implementing new features or making significant changes, create a detailed specification:

### Creating a Specification
1. Use `/new-spec [name]` to create a new specification from template
2. Or manually copy `specifications/TEMPLATE.md` to `specifications/[feature-name].md`
3. Fill out all relevant sections in the specification
4. Review with stakeholders before implementation

### Viewing Specifications
- Use `/list-specs` to see all existing specifications
- Specifications are stored in the `/specifications` directory

### Implementation Process
1. Always create a specification first for non-trivial features
2. Get the specification reviewed and approved
3. Use the specification as your implementation guide
4. Update the specification if requirements change during implementation
5. Check off acceptance criteria as you complete them

## Common Development Tasks

### Adding a New Alert Plugin
1. Create new file in `alert_plugins/` (e.g., `webhook_alert.py`)
2. Inherit from `BaseAlertPlugin` and implement required methods
3. Define `CONFIG_SCHEMA` for validation
4. Plugin will be automatically discovered and loaded

### Modifying Database Schema
1. Update models in `models.py`
2. Create migration if using PostgreSQL in production
3. For development with SQLite, database is recreated on startup

### API Development
- All API endpoints return JSON with consistent error format
- Use `@api.route()` decorator for API endpoints
- Application UUIDs are generated server-side for security

## Testing Guidelines

### Test Structure
- Tests use Flask test client with in-memory SQLite database
- Each test gets a fresh database via `client` fixture
- Mock external services (email, SMS, webhooks) in tests

### Running Specific Tests
```bash
# Run all tests in a file
uv run pytest tests/test_basic.py

# Run specific test method
uv run pytest tests/test_basic.py::test_post_application

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

## Docker Deployment
```bash
# Using docker-compose (includes optional PostgreSQL)
docker-compose up

# Build only
docker build -t heartbeat-central .

# Run with environment file
docker run --env-file .env -p 5000:5000 heartbeat-central
```

## Environment Configuration

Key environment variables (see `.env.example`):
- `DATABASE_URL`: SQLite or PostgreSQL connection string
- `HEARTBEAT_CHECK_INTERVAL`: How often to check for missed heartbeats (seconds)
- `SECRET_KEY`: Flask session secret
- Alert-specific configs (SMTP, Twilio, etc.)

## Benefits
- Clear requirements before coding
- Better design decisions
- Fewer surprises during implementation
- Built-in documentation
- Easier code reviews