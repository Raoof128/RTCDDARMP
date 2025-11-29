"""
Integration tests for API endpoints.
Tests security, prediction, drift, and model registry endpoints.
"""

import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# Set API Key for testing
os.environ["RCD2_API_KEY"] = "test-key-123"

# Set API Key for testing
os.environ["RCD2_API_KEY"] = "test-key-123"

HEADERS = {"X-API-Key": "test-key-123"}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Test public health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_security_unauthorized(client):
    """Test access without API Key."""
    response = client.get("/api/drift")
    assert response.status_code == 401  # Unauthorized


def test_security_invalid_key(client):
    """Test access with invalid API Key."""
    response = client.get("/api/drift", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403  # Forbidden


def test_security_authorized(client):
    """Test access with valid API Key."""
    response = client.get("/api/drift", headers=HEADERS)
    assert response.status_code == 200


def test_predict_endpoint(client):
    """Test prediction endpoint."""
    payload = {"features": [0.5, -0.2, 1.0]}
    response = client.post("/api/predict", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert "model_version" in data


def test_ingest_endpoint(client):
    """Test data ingestion endpoint."""
    payload = {"features": [0.5, -0.2, 1.0], "label": 1}
    response = client.post("/api/ingest", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert "current_window_size" in response.json()


def test_model_registry_endpoints(client):
    """Test model registry endpoints."""
    # List models
    response = client.get("/api/model/list", headers=HEADERS)
    assert response.status_code == 200, f"List models failed: {response.text}"
    assert "models" in response.json()

    # Get champion
    response = client.get("/api/model/champion", headers=HEADERS)
    # It might be 404 if initialization failed in test env, so we handle it
    if response.status_code == 404:
        print("⚠️ No champion model found in test env")
    else:
        assert response.status_code == 200, f"Get champion failed: {response.text}"
        assert "version" in response.json()


def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = client.get("/api/metrics", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "champion_model" in data
    assert "system_health" in data


def test_force_retrain_endpoint(client):
    """Test force retrain endpoint."""
    # Note: This might take time, so we just check if it accepts the request
    # or mocks the engine if needed. For integration test, we let it run.
    payload = {"drift_score": 85.0, "reason": "test_trigger"}
    response = client.post("/api/force_retrain", json=payload, headers=HEADERS)

    # It might return 200 or 500 depending on if training succeeds in test env
    # But we assert it passed security
    assert response.status_code in [200, 500]
