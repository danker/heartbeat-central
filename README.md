# Heartbeat Central

A Flask-based centralized heartbeat monitoring service with configurable alerts through multiple channels (email, Slack, Discord, SMS).

## Features

- **Heartbeat Monitoring**: Applications send periodic heartbeats to indicate they're alive
- **Application Management**: Register and manage applications via web interface or API
- **Missed Heartbeat Detection**: Automatic detection when applications fail to send heartbeats
- **Grace Periods**: Configurable grace periods before triggering alerts
- **Pluggable Alerts**: Email, Slack, Discord, and SMS notifications
- **Web Dashboard**: Manage applications and view heartbeat status
- **REST API**: Full API for programmatic management
- **Heartbeat History**: Track when applications last sent heartbeats
- **Background Monitoring**: Continuous monitoring service for missed heartbeats

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

5. **Register an application**:
   - Use the web interface to add a new application
   - Note the generated UUID for your application

6. **Send heartbeats**:
   ```bash
   curl -X POST http://localhost:5000/heartbeat/YOUR-APP-UUID
   ```

## How It Works

### 1. Application Registration
Register your applications with Heartbeat Central, specifying:
- **Name**: Human-readable application name
- **Expected Interval**: How often the application should send heartbeats (in seconds)
- **Grace Period**: Additional time to wait before considering the application down

### 2. Heartbeat Sending
Applications send periodic POST requests to `/heartbeat/{uuid}` to indicate they're alive.

### 3. Monitoring
The background service continuously monitors for applications that haven't sent heartbeats within their expected intervals plus grace periods, and triggers alerts when applications are overdue.

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `HEARTBEAT_CHECK_INTERVAL`: How often to check for missed heartbeats (default: 30 seconds)
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
  "username": "HeartbeatBot"
}
```

#### Discord
```json
{
  "webhook_url": "https://discord.com/api/webhooks/...",
  "username": "HeartbeatBot"
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

### Heartbeat Endpoint
- `POST /heartbeat/{uuid}` - Receive heartbeat from application

### Application Management
- `GET /api/applications` - List all applications
- `POST /api/applications` - Create new application
- `GET /api/applications/{id}` - Get specific application
- `PUT /api/applications/{id}` - Update application
- `DELETE /api/applications/{id}` - Delete application
- `GET /api/applications/{id}/heartbeats` - Get heartbeat history

### System Health
- `GET /health` - Health check endpoint for load balancers

## Integration Examples

### Python Application
```python
import requests
import time
import os

HEARTBEAT_URL = "http://heartbeat-central:5000/heartbeat/YOUR-APP-UUID"
INTERVAL = 60  # Send heartbeat every 60 seconds

def send_heartbeat():
    try:
        response = requests.post(HEARTBEAT_URL, timeout=5)
        if response.status_code == 200:
            print("Heartbeat sent successfully")
        else:
            print(f"Heartbeat failed: {response.status_code}")
    except Exception as e:
        print(f"Heartbeat error: {e}")

# Send heartbeat in your application loop
while True:
    send_heartbeat()
    time.sleep(INTERVAL)
```

### Docker Healthcheck
```dockerfile
HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://heartbeat-central:5000/heartbeat/YOUR-APP-UUID || exit 1
```

### Cron Job
```bash
# Send heartbeat every 5 minutes
*/5 * * * * curl -X POST http://heartbeat-central:5000/heartbeat/YOUR-APP-UUID
```

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
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Production Configuration
- Set `FLASK_ENV=production`
- Ensure proper `SECRET_KEY` is set
- Configure `HEARTBEAT_CHECK_INTERVAL` based on your needs
- Use a production database (PostgreSQL recommended)

## Architecture

- **Flask App**: Web server and API
- **SQLAlchemy**: Database ORM with SQLite default
- **APScheduler**: Background job scheduling for missed heartbeat detection
- **Alert Plugins**: Modular notification system
- **Bootstrap**: Responsive web interface

## Migration from Healthcheck Monitoring

If you're migrating from traditional healthcheck monitoring:
1. Replace active endpoint polling with heartbeat sending in your applications
2. Register each application in Heartbeat Central
3. Update your applications to send periodic heartbeats
4. Configure alerts for each application as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request