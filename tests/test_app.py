import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert all("description" in v for v in data.values())

def test_signup_and_duplicate():
    # Use a unique email for test
    email = "pytestuser@example.com"
    activity = next(iter(client.get("/activities").json().keys()))
    # First signup should succeed
    resp1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp1.status_code == 200
    # Duplicate signup should fail
    resp2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json()["detail"]

def test_signup_activity_not_found():
    resp = client.post("/activities/NonexistentActivity/signup?email=foo@bar.com")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

def test_signup_activity_full(monkeypatch):
    activity = next(iter(client.get("/activities").json().keys()))
    # Patch the activity to have max_participants = 0
    from src import app as app_module
    app_module.activities[activity]["max_participants"] = 0
    resp = client.post(f"/activities/{activity}/signup?email=fulltest@example.com")
    assert resp.status_code == 400
    assert "full" in resp.json()["detail"].lower()
    # Restore max_participants
    app_module.activities[activity]["max_participants"] = 10

def test_unregister_participant():
    activity = next(iter(client.get("/activities").json().keys()))
    email = "unregtest@example.com"
    # Register first
    client.post(f"/activities/{activity}/signup?email={email}")
    # Unregister
    resp = client.delete(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code in (200, 204)
    # Unregister again should fail
    resp2 = client.delete(f"/activities/{activity}/signup?email={email}")
    assert resp2.status_code == 404 or resp2.status_code == 400
