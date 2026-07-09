import os
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from backend.app.services.admin_service import AdminService
from backend.app.models import User, Camera, ActivityLog, Violation


class TestAdminService(unittest.TestCase):
    def setUp(self):
        self.admin_service = AdminService()
        self.db = MagicMock(spec=Session)

    @patch("backend.app.services.admin_service.admin_context_service.get_context")
    def test_get_dashboard_summary(self, mock_get_context):
        # Setup context mock
        mock_ctx = MagicMock()
        mock_ctx.total_vehicles = 150
        mock_ctx.total_violations = 120
        mock_ctx.total_cameras = 10
        mock_ctx.online_cameras = 8
        mock_ctx.total_users = 5
        mock_ctx.active_users = 4
        mock_ctx.system_status = {"cpu_percent": 12.5}
        mock_ctx.ocr_statistics = {"requests_count": 100}
        mock_ctx.email_statistics = {"total_emails": 50}

        mock_get_context.return_value = mock_ctx

        res = self.admin_service.get_dashboard_summary(self.db)
        self.assertEqual(res["total_vehicles"], 150)
        self.assertEqual(res["total_violations"], 120)
        self.assertEqual(res["total_cameras"], 10)
        self.assertEqual(res["online_cameras"], 8)
        self.assertEqual(res["total_users"], 5)
        self.assertEqual(res["active_users"], 4)
        mock_get_context.assert_called_once()

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("time.time")
    @patch("backend.app.services.admin_service.START_TIME", 1717100000.0)
    def test_get_system_status(self, mock_time, mock_disk, mock_mem, mock_cpu):
        mock_cpu.return_value = 45.2
        
        mem_mock = MagicMock()
        mem_mock.percent = 60.5
        mem_mock.used = 8 * 1024 * 1024 * 1024
        mem_mock.total = 16 * 1024 * 1024 * 1024
        mock_mem.return_value = mem_mock

        disk_mock = MagicMock()
        disk_mock.percent = 30.1
        disk_mock.used = 150 * 1024 * 1024 * 1024
        disk_mock.total = 500 * 1024 * 1024 * 1024
        mock_disk.return_value = disk_mock

        mock_time.return_value = 1717171717.0

        res = self.admin_service.get_system_status()
        self.assertEqual(res["cpu_percent"], 45.2)
        self.assertEqual(res["memory_percent"], 60.5)
        self.assertEqual(res["memory_used_gb"], 8.0)
        self.assertEqual(res["disk_percent"], 30.1)
        self.assertEqual(res["disk_used_gb"], 150.0)
        self.assertEqual(res["uptime_seconds"], 71717.0)

    def test_list_cameras(self):
        cam = Camera(
            id="cam-1",
            name="North Intersection",
            location="Zone A",
            ip_address="192.168.1.50",
            status="online",
            health_status="good",
            lat=40.7128,
            lng=-74.0060
        )
        self.db.query().all.return_value = [cam]

        # Patch camera_manager attributes
        with patch("backend.app.services.admin_service.camera_manager") as mock_cm:
            mock_cm.current_source = "cam-1"
            mock_cm.actual_fps = 30.0
            mock_cm.width = 1920
            mock_cm.height = 1080

            res = self.admin_service.list_cameras(self.db)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["id"], "cam-1")
            self.assertEqual(res[0]["name"], "North Intersection")
            self.assertTrue(res[0]["is_active_feed"])
            self.assertEqual(res[0]["fps"], 30.0)
            self.assertEqual(res[0]["resolution"], "1920x1080")

    def test_toggle_camera_not_found(self):
        self.db.query().filter().first.return_value = None
        success = self.admin_service.toggle_camera(self.db, "cam-99", False, 1)
        self.assertFalse(success)

    def test_toggle_camera_success(self):
        cam = Camera(id="cam-1", status="online")
        self.db.query().filter().first.return_value = cam

        success = self.admin_service.toggle_camera(self.db, "cam-1", False, 1)
        self.assertTrue(success)
        self.assertEqual(cam.status, "offline")
        self.db.commit.assert_called()

    def test_restart_camera_not_found(self):
        self.db.query().filter().first.return_value = None
        success = self.admin_service.restart_camera(self.db, "cam-99", 1)
        self.assertFalse(success)

    def test_restart_camera_success(self):
        cam = Camera(id="cam-1", status="offline", ip_address="192.168.1.10")
        self.db.query().filter().first.return_value = cam

        with patch("backend.app.services.admin_service.camera_manager") as mock_cm:
            mock_cm.current_source = "cam-1"
            mock_cm.is_connected = True

            success = self.admin_service.restart_camera(self.db, "cam-1", 1)
            self.assertTrue(success)
            mock_cm.disconnect.assert_called_once()
            mock_cm.connect.assert_called_once()

    def test_list_users(self):
        user = User(
            id=2,
            username="officer_smith",
            email="smith@city.gov",
            full_name="Officer Smith",
            role="officer",
            status="active"
        )
        self.db.query().all.return_value = [user]

        res = self.admin_service.list_users(self.db)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["username"], "officer_smith")
        self.assertEqual(res[0]["role"], "officer")

    def test_update_user_status_not_found(self):
        self.db.query().filter().first.return_value = None
        success = self.admin_service.update_user_status(self.db, 99, "viewer", "inactive", 1)
        self.assertFalse(success)

    def test_update_user_status_success(self):
        user = User(id=2, role="officer", status="active")
        self.db.query().filter().first.return_value = user

        success = self.admin_service.update_user_status(self.db, 2, "admin", "inactive", 1)
        self.assertTrue(success)
        self.assertEqual(user.role, "admin")
        self.assertEqual(user.status, "inactive")
        self.db.commit.assert_called()

    def test_get_settings(self):
        with patch("backend.app.services.admin_service.settings") as mock_settings, \
             patch("backend.app.services.admin_service.pipeline_manager") as mock_pm:
            
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_EMAIL = "test@gmail.com"
            mock_settings.SMTP_APP_PASSWORD = "pass"
            mock_settings.SMTP_USE_TLS = True
            mock_settings.EMAIL_FROM = "sender@gmail.com"
            mock_settings.AI_CONFIDENCE_THRESHOLD = 0.5
            mock_settings.SPEED_LIMIT_KMH = 60.0
            mock_settings.UPLOAD_DIR = "/tmp/evidence"
            mock_pm.enabled_modules = ["ocr"]

            res = self.admin_service.get_settings()
            self.assertEqual(res["smtp"]["host"], "smtp.gmail.com")
            self.assertEqual(res["ai"]["speed_limit_kmh"], 60.0)
            self.assertEqual(res["upload_dir"], "/tmp/evidence")

    @patch("yaml.safe_load")
    @patch("yaml.safe_dump")
    @patch("builtins.open")
    @patch("os.path.exists")
    def test_update_settings(self, mock_exists, mock_open, mock_dump, mock_load):
        mock_exists.return_value = True
        mock_load.return_value = {"modules": {"ocr": {"enabled": False}}}
        payload = {
            "smtp": {"host": "new.smtp.com"},
            "ai": {"confidence_threshold": 0.7, "enabled_modules": ["ocr"]}
        }
        with patch("backend.app.services.admin_service.settings") as mock_settings, \
             patch("backend.app.services.admin_service.pipeline_manager") as mock_pm:
            
            mock_pm.execution_order = ["ocr"]
            success = self.admin_service.update_settings(payload, 1, self.db)
            self.assertTrue(success)
            mock_dump.assert_called()
            self.db.add.assert_called()

    def test_list_modules(self):
        with patch("backend.app.services.admin_service.pipeline_manager") as mock_pm, \
             patch("backend.app.services.admin_service.module_registry") as mock_reg:
            
            mock_pm.enabled_modules = ["vehicle_detection"]
            mock_mod = MagicMock()
            mock_mod.health.return_value = True
            mock_reg.get.return_value = mock_mod

            res = self.admin_service.list_modules()
            self.assertTrue(len(res) > 0)
            self.assertEqual(res[0]["name"], "vehicle_detection")
            self.assertEqual(res[0]["status"], "Loaded")

    @patch("os.path.exists")
    @patch("os.walk")
    def test_get_storage_status(self, mock_walk, mock_exists):
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("/path/to/evidence", [], ["file1.jpg", "file2.mp4"])
        ]
        # mock stat size
        with patch("os.path.getsize", return_value=50 * 1024 * 1024):
            res = self.admin_service.get_storage_status()
            self.assertEqual(res["total_size_mb"], 100.0) # 2 files * 50MB = 100MB
            self.assertEqual(res["files_count"], 2)

    @patch("builtins.open")
    @patch("os.path.exists")
    def test_get_recent_logs(self, mock_exists, mock_open):
        mock_exists.return_value = True
        file_mock = MagicMock()
        file_mock.readlines.return_value = ["Line 1\n", "Line 2\n"]
        mock_open.return_value.__enter__.return_value = file_mock

        res = self.admin_service.get_recent_logs(10)
        self.assertEqual(res["total_lines"], 2)
        self.assertEqual(res["lines"], ["Line 1", "Line 2"])

    def test_list_audit_logs(self):
        log = ActivityLog(
            id=1,
            user_id=1,
            action="Config update",
            timestamp=None
        )
        # Mock pagination query
        self.db.query().order_by().offset().limit().all.return_value = [log]

        res = self.admin_service.list_audit_logs(self.db, 1, 10)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["action"], "Config update")

    @patch("backend.app.services.admin_service.admin_service.get_system_status")
    def test_get_health_status(self, mock_sys):
        mock_sys.return_value = {"cpu_percent": 30.0, "memory_percent": 50.0}
        
        # Test healthy
        self.db.execute = MagicMock()
        res = self.admin_service.get_health_status()
        self.assertTrue(res["database"])
        self.assertTrue(res["system_resources"])
        self.assertTrue(res["api_health"])
