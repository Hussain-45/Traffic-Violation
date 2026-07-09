from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_camera_sources():
    response = client.get("/api/v1/camera/sources")
    assert response.status_code == 200
    assert response.json() == ["Webcam", "Video File", "IP Camera", "RTSP"]

def test_camera_status():
    response = client.get("/api/v1/camera/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
    assert "fps" in data
    assert "width" in data
    assert "height" in data
    assert "source_type" in data

def test_camera_connect_and_disconnect():
    # Attempt to connect to webcam index 0 (which is the default or simulated)
    response = client.post("/api/v1/camera/connect", json={"source": 0})
    # Note: connect might succeed or fall back depending on the device,
    # but the API response should be 200 OK or 400 Bad Request depending on hw availability.
    # We will test if disconnect works:
    assert response.status_code in [200, 400]
    
    response_disconnect = client.post("/api/v1/camera/disconnect")
    assert response_disconnect.status_code == 200
    assert response_disconnect.json() == {
        "status": "success", 
        "message": "Camera disconnected successfully"
    }
