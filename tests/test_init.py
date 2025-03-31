"""
Test Application Initialization
"""
import unittest
from unittest.mock import patch
from flask import Flask
from service import create_app


class TestInitialization(unittest.TestCase):
    """Test application initialization process"""

    @patch('service.models.db')
    def test_create_app_success(self, mock_db):
        """Test the create_app function - successful path"""
        app = create_app()
        self.assertIsInstance(app, Flask)
        self.assertTrue(mock_db.create_all.called)

    @patch('service.sys.exit')
    @patch('service.models.db.create_all')
    def test_create_app_failure(self, mock_create_all, mock_exit):
        """Test the create_app function when db.create_all fails"""
        # Set up the test to force an exception in db.create_all
        mock_create_all.side_effect = Exception("Test DB creation error")

        # Call create_app which should catch the exception and exit
        create_app()

        # Verify that sys.exit was called with exit code 4
        mock_exit.assert_called_once_with(4)

    @patch('service.log_handlers.init_logging')
    def test_init_logging_called(self, mock_init_logging):
        """Test that logging initialization is called"""
        create_app()
        mock_init_logging.assert_called_once()
