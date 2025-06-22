"""Basic tests for the heartbeat monitor application."""

import pytest

from app import app
from database import db
from models import Application


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


def test_api_applications_get(client):
    """Test getting applications via API."""
    response = client.get("/api/applications")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)


def test_api_applications_post(client):
    """Test creating an application via API."""
    payload = {
        "name": "Test Application",
        "expected_interval": 300,
        "grace_period": 30,
    }

    response = client.post("/api/applications", json=payload)
    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()
    assert data["name"] == "Test Application"
    assert data["expected_interval"] == 300
    assert "uuid" in data


def test_api_applications_post_invalid(client):
    """Test creating an application with invalid data."""
    payload = {"name": "Test"}  # Missing required expected_interval

    response = client.post("/api/applications", json=payload)
    assert response.status_code == 400


def test_application_model():
    """Test the Application model."""
    app = Application(
        name="Test Application",
        expected_interval=300,
        grace_period=30,
    )

    assert app.name == "Test Application"
    assert app.expected_interval == 300
    assert app.grace_period == 30

    # Test to_dict method
    data = app.to_dict()
    assert data["name"] == "Test Application"
    assert data["expected_interval"] == 300
    assert "uuid" in data


def test_heartbeat_endpoint_invalid_uuid(client):
    """Test heartbeat endpoint with invalid UUID."""
    response = client.post("/heartbeat/invalid-uuid")
    assert response.status_code == 404  # Flask will return 404 for invalid UUID format
