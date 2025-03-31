"""
Test Error Handlers
"""
import json
from unittest import TestCase
from unittest.mock import patch
# Fix the import to get app from the correct location
from service.routes import app  # Import from routes.py instead
from service.common import status


class TestErrorHandlers(TestCase):
    """Test Error Handlers"""

    def setUp(self):
        """Set up the test case"""
        self.app = app.test_client()

    def test_not_found(self):
        """It should handle resource not found errors"""
        resp = self.app.get("/not-found-route")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Not Found")

    def test_method_not_allowed(self):
        """It should handle method not allowed errors"""
        # Try to POST to a GET-only endpoint
        resp = self.app.post("/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Method not Allowed")

    def test_unsupported_media_type(self):
        """It should handle unsupported media type errors"""
        # POST with text/plain content type
        resp = self.app.post(
            "/shopcarts/1",
            headers={"Content-Type": "text/plain"},
            data="plain text instead of JSON"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Unsupported media type")

    def test_bad_request(self):
        """It should handle bad request errors"""
        # Send a request that will trigger a 400 Bad Request
        resp = self.app.post(
            "/shopcarts",
            json={"invalid": "data", "user_id": "not-an-integer"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Bad Request")

    def test_internal_server_error(self):
        """It should handle internal server errors"""
        # We need to mock a service method to force a 500 error
        with patch("service.models.Shopcart.all", side_effect=Exception("Database error")):
            resp = self.app.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = json.loads(resp.data)
            self.assertIn("status", data)
            self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal Server Error")
