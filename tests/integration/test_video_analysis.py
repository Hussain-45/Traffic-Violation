import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import os
import io

from backend.main import app
from backend.app.database import get_db
from backend.app.models import User
from backend.app.models.video_analysis_model import AnalysisJob
from backend.app.services.password_service import password_service

class TestVideoAnalysisAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db_mock = MagicMock(spec=Session)
        app.dependency_overrides[get_db] = lambda: self.db_mock

        # Setup mock user
        raw_pass = "SecurePass123!"
        hashed_pass = password_service.hash_password(raw_pass)
        self.mock_user = User(
            id=1,
            username="security_officer",
            email="officer@stvds.gov",
            full_name="Security Officer",
            password_hash=hashed_pass,
            status="active",
            role="admin",
            failed_login_attempts=0,
            locked_until=None
        )

        # Mock DB queries to return mock user
        self.db_mock.query().filter().first.return_value = self.mock_user

        # Get JWT token
        login_res = self.client.post(
            "/api/v1/auth/login",
            json={"username": "security_officer", "password": raw_pass}
        )
        self.assertEqual(login_res.status_code, 200)
        self.token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("backend.app.routes.video_analysis.cv2.VideoCapture")
    def test_upload_video_endpoint(self, mock_video_capture):
        # Configure cv2 VideoCapture mock
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 0, # CAP_PROP_POS_MSEC
            3: 640, # CAP_PROP_FRAME_WIDTH
            4: 480, # CAP_PROP_FRAME_HEIGHT
            5: 30, # CAP_PROP_FPS
            7: 150 # CAP_PROP_FRAME_COUNT
        }.get(prop, 0)
        mock_video_capture.return_value = mock_cap

        # Create dummy file bytes representing video
        dummy_video = io.BytesIO(b"Fake MP4 video file bytes")
        
        # Call upload endpoint
        response = self.client.post(
            "/api/v1/video/upload",
            headers=self.headers,
            files={"file": ("test_video.mp4", dummy_video, "video/mp4")}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["filename"], "test_video.mp4")
        self.assertEqual(data["resolution"], "640x480")
        self.assertEqual(data["fps"], 30)
        self.assertEqual(data["duration"], 5.0)

    def test_get_jobs_endpoint(self):
        import datetime
        # Mock query return
        mock_job = AnalysisJob(
            id=42,
            filename="test_video.mp4",
            original_video_path="data/uploads/videos/input/test.mp4",
            status="pending",
            progress=0.0,
            total_frames=150,
            processed_frames=0,
            vehicles_detected=0,
            violations_detected=0,
            processing_fps=0.0,
            processing_time=0.0,
            created_by=1,
            created_at=datetime.datetime.utcnow()
        )
        self.db_mock.query().order_by().all.return_value = [mock_job]

        response = self.client.get("/api/v1/video/jobs", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["filename"], "test_video.mp4")
        self.assertEqual(data[0]["status"], "pending")
