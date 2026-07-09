import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.app.database import get_db
from backend.app.models import User
from backend.app.services.password_service import password_service
from backend.app.services.jwt_service import jwt_service


class TestIntegrationE2EPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db_mock = MagicMock(spec=Session)

        # Mock DB dependency globally
        app.dependency_overrides[get_db] = lambda: self.db_mock

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_e2e_authentication_and_health_flow(self):
        # 1. Setup mock user with bcrypt password hash
        raw_pass = "SecurePass123!"
        hashed_pass = password_service.hash_password(raw_pass)
        mock_user = User(
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

        # Configure DB mock queries
        self.db_mock.query().filter().first.return_value = mock_user

        # 2. Trigger Login request
        login_res = self.client.post(
            "/api/v1/auth/login",
            json={"username": "security_officer", "password": raw_pass}
        )
        self.assertEqual(login_res.status_code, 200)
        tokens = login_res.json()
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)

        # 3. Access current profile protected route
        access_token = tokens["access_token"]
        me_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(me_res.status_code, 200)
        profile = me_res.json()
        self.assertEqual(profile["username"], "security_officer")
        self.assertEqual(profile["role"], "admin")

        # 4. Trigger Health Check diagnostic endpoint
        health_res = self.client.get(
            "/api/v1/admin/health",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(health_res.status_code, 200)
        health_data = health_res.json()
        self.assertEqual(health_data["status"], "ok")
        self.assertTrue(health_data["database"])
        self.assertTrue(health_data["api_health"])
