"""
Test Error Handlers
"""
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock
# Fix the import to get app from the correct location
from service.routes import app  # Import from routes.py instead
from service.common import status, error_handlers
from service.models import DataValidationError


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
        resp = self.app.post(
            "/shopcarts/1/items",
            json={"invalid": "data", "quantity": -10},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.data)
        # Updated expected error message:
        self.assertEqual(data["error"], "Invalid input: 'product_id'")

    def test_internal_server_error(self):
        """It should handle internal server errors"""
        with patch("service.controllers.get_controller.Shopcart.all", side_effect=Exception("Database error")):
            resp = self.app.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = json.loads(resp.data)
            # Expect the error handler to wrap the exception with a uniform message:
            self.assertEqual(data["error"], "Internal Server Error")

    def test_database_connection_error(self):
        """It should handle database connection errors"""
        with patch("service.controllers.get_controller.Shopcart.all",
                   side_effect=error_handlers.DatabaseConnectionError("DB Connection Error")):
            resp = self.app.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            data = json.loads(resp.data)
            self.assertEqual(data["error"], "Service Unavailable")
            self.assertEqual(data["message"], "DB Connection Error")

    # Direct tests for error handler functions to increase coverage
    def test_method_not_allowed_direct(self):
        """Test direct call to method_not_allowed handler (covers line 36)"""
        # Create a mock error with a description
        mock_error = MagicMock()
        mock_error.description = "Method not allowed test"

        # Call the handler function directly
        response, status_code = error_handlers.method_not_supported(mock_error)

        # Verify the response
        self.assertEqual(status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["error"], "Method not Allowed")
        self.assertEqual(data["message"], "Method not allowed test")

    def test_bad_request_direct(self):
        """Test direct call to bad_request handler (covers lines 42-44)"""
        # Test with a string error
        response, status_code = error_handlers.bad_request("Simple error")
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["error"], "Bad Request")
        self.assertEqual(data["message"], "Simple error")

        # Test with a DataValidationError (to cover the request_validation_error handler)
        validation_error = DataValidationError("Invalid data format")
        response, status_code = error_handlers.request_validation_error(validation_error)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["message"], "Invalid data format")

        # Test with a different error object
        # Define a properly documented class with sufficient methods to avoid linting issues
        class CustomError:
            """Custom error class for testing error handler's string conversion."""

            def __str__(self):
                """Return a string representation of the error."""
                return "Custom error message"

            def get_message(self):
                """Additional method to avoid too-few-public-methods linting error."""
                return self.__str__()

        custom_error = CustomError()
        response, status_code = error_handlers.bad_request(custom_error)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["message"], "Custom error message")
