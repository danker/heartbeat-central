# Healthcheck Monitor

A Flask-based application for monitoring website health with configurable alerts through multiple channels (email, Slack, Discord, SMS).

## Features

- **Endpoint Monitoring**: Monitor HTTP endpoints with customizable intervals
- **Text Matching**: Verify expected content is present in responses
- **Pluggable Alerts**: Email, Slack, Discord, and SMS notifications
- **Web Dashboard**: Manage healthchecks through a web interface
- **REST API**: Full API for programmatic management
- **Scheduling**: Automatic periodic health checks
- **History Tracking**: View historical check results

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the dashboard**:
   Open http://localhost:5000 in your browser

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SMTP_*`: Email server configuration
- `TWILIO_*`: SMS configuration via Twilio

### Alert Plugins

#### Email
```json
{
  "to_email": "admin@example.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your-email@gmail.com",
  "password": "your-app-password"
}
```

#### Slack
```json
{
  "webhook_url": "https://hooks.slack.com/services/...",
  "channel": "#alerts",
  "username": "HealthcheckBot"
}
```

#### Discord
```json
{
  "webhook_url": "https://discord.com/api/webhooks/...",
  "username": "HealthcheckBot"
}
```

#### SMS
```json
{
  "to_number": "+1234567890",
  "account_sid": "your-twilio-sid",
  "auth_token": "your-twilio-token",
  "from_number": "+1987654321"
}
```

## API Endpoints

- `GET /api/healthchecks` - List all healthchecks
- `POST /api/healthchecks` - Create new healthcheck
- `GET /api/healthchecks/{id}` - Get specific healthcheck
- `PUT /api/healthchecks/{id}` - Update healthcheck
- `DELETE /api/healthchecks/{id}` - Delete healthcheck
- `POST /api/healthchecks/{id}/check` - Trigger manual check
- `GET /api/healthchecks/{id}/results` - Get check history
- `GET /api/healthchecks/{id}/alerts` - Get alert configurations
- `POST /api/healthchecks/{id}/alerts` - Add alert configuration
- `DELETE /api/alerts/{id}` - Delete alert configuration

## Development

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```

### Code Formatting
```bash
black .
flake8 .
```

## Deployment

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Production Configuration
Set `FLASK_ENV=production` and ensure proper `SECRET_KEY` is set.

## Architecture

- **Flask App**: Web server and API
- **SQLAlchemy**: Database ORM with SQLite default
- **APScheduler**: Background job scheduling
- **Alert Plugins**: Modular notification system
- **Bootstrap**: Responsive web interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request