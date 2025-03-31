"""
Test Error Handlers
"""
import json
from unittest import TestCase
from werkzeug.exceptions import (
    InternalServerError,
    BadRequest,
    Conflict
)
from service import app
from service.common import status
from service.models import DatabaseConnectionError, DataValidationError


class TestErrorHandlers(TestCase):
    """Test Error Handlers"""

    def setUp(self):
        """Set up the test case"""
        self.app = app.test_client()

    def test_not_found(self):
        """It should handle resource not found errors"""
        resp = self.app.get("/not-found")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Not Found")

    def test_method_not_allowed(self):
        """It should handle method not allowed errors"""
        # Create a route that only supports GET
        @app.route("/method-test", methods=["GET"])
        def method_test():
            return "OK"

        # Try to call it with POST
        resp = self.app.post("/method-test")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Method not Allowed")

    def test_unsupported_media_type(self):
        """It should handle unsupported media type errors"""
        # Force an UnsupportedMediaType error
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

    def test_conflict_request(self):
        """It should handle conflict errors"""
        # Create a route that raises Conflict
        @app.route("/conflict-test")
        def conflict_test():
            raise Conflict("Testing conflict error handler")

        resp = self.app.get("/conflict-test")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_409_CONFLICT)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Conflict")

    def test_database_connection_error(self):
        """It should handle database connection errors"""
        # Create a route that raises DatabaseConnectionError
        @app.route("/db-error-test")
        def db_error_test():
            raise DatabaseConnectionError("Testing database connection error handler")

        resp = self.app.get("/db-error-test")
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Service Unavailable")

    def test_data_validation_error(self):
        """It should handle data validation errors"""
        # Create a route that raises DataValidationError
        @app.route("/data-validation-test")
        def data_validation_test():
            raise DataValidationError("Testing data validation error handler")

        resp = self.app.get("/data-validation-test")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Bad Request")

    def test_internal_server_error(self):
        """It should handle internal server errors"""
        # Create a route that raises an internal server error
        @app.route("/server-error-test")
        def server_error_test():
            raise InternalServerError("Testing internal server error handler")

        resp = self.app.get("/server-error-test")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Internal Server Error")
