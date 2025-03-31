"""
Test Error Handlers
"""
import json
from unittest import TestCase
from werkzeug.exceptions import (
    BadRequest,
    InternalServerError,
)
from service import app
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
        # Create a route that raises BadRequest
        @app.route("/bad-request-test")
        def bad_request_test():
            raise BadRequest("Testing bad request error handler")

        resp = self.app.get("/bad-request-test")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Bad Request")

    def test_internal_server_error(self):
        """It should handle internal server errors"""
        # Create a route that raises an exception
        @app.route("/server-error-test")
        def server_error_test():
            raise InternalServerError("Testing server error handler")

        resp = self.app.get("/server-error-test")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Internal Server Error")
