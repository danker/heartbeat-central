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


def test_api_applications_post_with_is_active(client):
    """Test creating an application with is_active field."""
    payload = {
        "name": "Test Application",
        "expected_interval": 300,
        "grace_period": 30,
        "is_active": False,
    }

    response = client.post("/api/applications", json=payload)
    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()
    assert data["name"] == "Test Application"
    assert data["is_active"] is False


def test_api_applications_put_is_active(client):
    """Test updating is_active field via PUT endpoint."""
    # First create an application
    payload = {
        "name": "Test Application",
        "expected_interval": 300,
        "grace_period": 30,
    }
    response = client.post("/api/applications", json=payload)
    app_data = response.get_json()
    app_id = app_data["id"]

    # Test deactivating
    update_payload = {"is_active": False}
    response = client.put(f"/api/applications/{app_id}", json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_active"] is False

    # Test reactivating
    update_payload = {"is_active": True}
    response = client.put(f"/api/applications/{app_id}", json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_active"] is True


def test_heartbeat_endpoint_inactive_application(client):
    """Test heartbeat endpoint with inactive application."""
    # Create an inactive application
    payload = {
        "name": "Inactive App",
        "expected_interval": 300,
        "is_active": False,
    }
    response = client.post("/api/applications", json=payload)
    app_data = response.get_json()
    app_uuid = app_data["uuid"]

    # Try to send heartbeat to inactive app
    response = client.post(f"/heartbeat/{app_uuid}")
    assert response.status_code == 400
    data = response.get_json()
    assert "not active" in data["error"].lower()


def test_dashboard_inactive_application_status(client):
    """Test that inactive applications show correct status on dashboard."""
    # Create an inactive application
    payload = {
        "name": "Inactive Dashboard App",
        "expected_interval": 300,
        "is_active": False,
    }
    client.post("/api/applications", json=payload)

    # Check dashboard response
    response = client.get("/")
    assert response.status_code == 200
    # The dashboard should render without error when inactive apps are present
    assert b"Inactive Dashboard App" in response.data


def test_application_model_default_active(client):
    """Test that Application model defaults to active=True."""
    with client.application.app_context():
        app = Application(
            name="Test Default Active",
            expected_interval=300,
        )
        db.session.add(app)
        db.session.commit()

        assert app.is_active is True

        # Test to_dict includes is_active
        data = app.to_dict()
        assert "is_active" in data
        assert data["is_active"] is True
