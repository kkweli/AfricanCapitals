import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import unittest
from fastapi.testclient import TestClient
from app.main import app

class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        # Optionally check response content
        # self.assertIn("status", response.json())

if __name__ == '__main__':
    unittest.main()