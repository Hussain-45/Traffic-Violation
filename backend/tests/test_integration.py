import unittest
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000/api/v1"

class TestEndToEndIntegration(unittest.TestCase):
    token = None

    @classmethod
    def setUpClass(cls):
        # 1. Authenticate and obtain JWT token
        login_url = f"{BASE_URL}/auth/login"
        data = urllib.parse.urlencode({
            "username": "admin",
            "password": "admin123"
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                login_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                cls.token = res_data.get("access_token")
                print("\n[SETUP] Successfully authenticated admin and retrieved JWT token.")
        except Exception as e:
            print(f"\n[SETUP ERROR] Make sure the FastAPI server is running at http://localhost:8000/ ({e})")
            cls.token = None

    def setUp(self):
        if not self.token:
            self.skipTest("FastAPI server is offline or authentication failed.")

    def test_01_get_cameras(self):
        # Verify camera listing and integration
        url = f"{BASE_URL}/cameras"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            self.assertTrue(len(data) > 0, "No cameras returned in database")
            print("[TEST] Connected to database and retrieved camera node lists successfully.")

    def test_02_get_violations(self):
        # Verify violations advanced search and filters integration
        url = f"{BASE_URL}/violations?limit=5"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIn("items", data)
            self.assertIsInstance(data["items"], list)
            print("[TEST] Advanced search API queried violations database records successfully.")

    def test_03_fine_rules(self):
        # Verify fine policy tariff mapping integrations
        url = f"{BASE_URL}/fines/rules"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            self.assertTrue(any(r["violation_type"] == "red_light_jump" for r in data))
            print("[TEST] Fine Rules tariff policies mapped successfully.")

    def test_04_notifications(self):
        # Verify notification alerts retrieval integration
        url = f"{BASE_URL}/notifications"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            print("[TEST] Notifications API synced alert history successfully.")

if __name__ == "__main__":
    unittest.main()
