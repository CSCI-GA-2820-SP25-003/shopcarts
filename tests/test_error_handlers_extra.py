"""Additional tests for error handlers to improve coverage."""

import unittest
from flask import Flask
from service.common import error_handlers, status
from service.common.error_handlers import internal_server_error


# Define a custom exception for testing
class TestServiceError(Exception):
    """Custom exception for testing error handlers."""
    pass


class TestErrorHandlersExtra(unittest.TestCase):
    """Test cases for direct exercise of error handler functions to improve coverage."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        # Register the error handlers defined in error_handlers.py.
        self.app.register_error_handler(Exception, error_handlers.handle_general_exception)
        self.client = self.app.test_client()

    def test_internal_server_error_handler_direct(self):
        """Directly call internal_server_error handler with a dummy exception."""
        error = TestServiceError("Test error")  # Use our custom exception
        # Call the handler directly.
        response, status_code = internal_server_error(error)
        self.assertEqual(status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.get_json()
        self.assertEqual(data["error"], "Internal Server Error")
        self.assertEqual(data["message"], "Test error")

    def test_general_exception_handler(self):
        """Test the general exception handler registered for all Exceptions."""
        # Cause an exception by requesting an unknown route in our test app.
        @self.app.route("/trigger-error")
        def trigger_error():
            # Use our custom exception instead of the general Exception
            raise TestServiceError("Triggered error")

        resp = self.client.get("/trigger-error")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")
        self.assertIn("Triggered error", data["message"])


if __name__ == '__main__':
    unittest.main()
