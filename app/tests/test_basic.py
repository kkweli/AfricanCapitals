import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @patch("httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_health(self, mock_get):
        # Mock all httpx GET requests to return a dummy response
        mock_response = AsyncMock()
        mock_response.status_code = 200  # Set status_code directly
        mock_response.text = AsyncMock(return_value="OK")
        mock_get.return_value = mock_response

        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()