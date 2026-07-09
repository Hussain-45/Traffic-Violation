from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Traffic Violation AI Backend Running"}

def test_check_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "Traffic Violation AI"
    assert "version" in response.json()

def test_404_handler():
    response = client.get("/non-existent-route-for-testing")
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "Not Found",
        "detail": None
    }
