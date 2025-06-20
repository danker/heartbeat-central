"""Basic tests for the healthcheck monitor application."""

import pytest

from app import app, db
from models import Healthcheck


@pytest.fixture
def client():
    """Create a test client."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["status"] == "healthy"


def test_dashboard_endpoint(client):
    """Test the dashboard endpoint."""
    response = client.get("/")
    assert response.status_code == 200


def test_api_healthchecks_get(client):
    """Test getting healthchecks via API."""
    response = client.get("/api/healthchecks")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)


def test_api_healthchecks_post(client):
    """Test creating a healthcheck via API."""
    payload = {
        "name": "Test Healthcheck",
        "url": "https://example.com",
        "expected_text": "Example",
        "check_interval": 300,
        "timeout": 30,
    }

    response = client.post("/api/healthchecks", json=payload)
    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()
    assert data["name"] == "Test Healthcheck"
    assert data["url"] == "https://example.com"


def test_api_healthchecks_post_invalid(client):
    """Test creating a healthcheck with invalid data."""
    payload = {"name": "Test"}  # Missing required URL

    response = client.post("/api/healthchecks", json=payload)
    assert response.status_code == 400


def test_healthcheck_model():
    """Test the Healthcheck model."""
    hc = Healthcheck(
        name="Test",
        url="https://example.com",
        expected_text="test",
        check_interval=300,
        timeout=30,
    )

    assert hc.name == "Test"
    assert hc.url == "https://example.com"
    assert hc.is_active is None  # Default is only applied when saved to DB

    # Test to_dict method
    data = hc.to_dict()
    assert data["name"] == "Test"
    assert data["url"] == "https://example.com"


def test_status_api(client):
    """Test the status API endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert "total_healthchecks" in data
    assert "healthy" in data
    assert "unhealthy" in data
    assert "unknown" in data
