"""Test file targeting remaining uncovered lines"""

import unittest
from unittest.mock import MagicMock
import service
from service.common import error_handlers
from service.common import log_handlers


class TestInitModule(unittest.TestCase):
    """Test case for init module functions"""

    def test_init_module(self):
        """Test init module initialization (coverage for __init__.py)"""
        # Just importing the module should execute the code
        self.assertIsNotNone(service.app)
        # Can add assertions about expected app configuration


class TestErrorHandlers(unittest.TestCase):
    """Test cases for error handler edge cases"""

    def test_method_not_allowed(self):
        """Test method not allowed handler"""
        error = MagicMock()
        error.description = "Method not allowed"

        response, code = error_handlers.method_not_allowed(error)
        data = response.get_json()

        self.assertEqual(code, 405)
        self.assertEqual(data["error"], "Method not allowed")
        self.assertEqual(data["message"], "Method not allowed")


class TestLogHandlers(unittest.TestCase):
    """Test cases for log handlers"""

    def test_init_logging(self):
        """Test log handler initialization"""
        # Correctly call init_logging with the required parameter
        logger = log_handlers.init_logging("test_module", "INFO")
        self.assertIsNotNone(logger)
        # Now use the logger (don't assign the result since info() doesn't return anything)
        logger.info("Test log message")  # This should exercise line 35


if __name__ == '__main__':
    unittest.main()
