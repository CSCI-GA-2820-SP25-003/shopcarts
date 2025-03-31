"""Tests specifically targeting uncovered sections of helpers.py"""

import unittest
from unittest.mock import patch, MagicMock
from service.common import helpers, status


class TestHelpersCoverage(unittest.TestCase):
    """Tests targeting specific uncovered parts of helpers.py"""

    def test_validate_request_data_noninteger_values(self):
        """Test validate_request_data with non-integer values (line ~139)"""
        # Test non-integer quantity
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "not-a-number",
                "name": "Test",
                "price": "10.0"
            })

        # Test non-integer stock
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "5",
                "name": "Test",
                "price": "10.0",
                "stock": "invalid"
            })

        # Test non-integer purchase_limit
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "5",
                "name": "Test",
                "price": "10.0",
                "purchase_limit": "invalid"
            })

    def test_update_or_create_cart_item_error_json_extraction(self):
        """Test update_or_create_cart_item error JSON extraction (lines ~165-173)"""
        # Create a mock cart item
        mock_cart_item = MagicMock()
        mock_cart_item.quantity = 5

        # Mock the find method
        with patch('service.common.helpers.Shopcart.find', return_value=mock_cart_item):
            # Mock validate_stock_and_limits to return an error response
            error_json = {"error": "Test error message"}
            mock_response = MagicMock()
            mock_response.json = error_json

            with patch('service.common.helpers.validate_stock_and_limits',
                       return_value=(mock_response, status.HTTP_400_BAD_REQUEST)):
                # This should cause the error extraction code to run
                with self.assertRaises(ValueError) as e:
                    helpers.update_or_create_cart_item(1, {
                        "product_id": 123,
                        "quantity": 10,
                        "name": "Test",
                        "price": 10.0,
                        "stock": 5,  # This will trigger the stock limit error
                        "purchase_limit": None
                    })
                self.assertEqual(str(e.exception), "Test error message")

    def test_extract_item_filters_uncovered_cases(self):
        """Test extract_item_filters with cases covering lines ~226-227, ~269-286"""
        # Test with field not in request_args but range_key in request_args (line ~269-270)
        args = {"quantity_range": "5,10"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "range")
        self.assertEqual(filters["quantity"]["value"], ["5", "10"])

        # Test with invalid range format (line ~278-282)
        args = {"quantity_range": "invalid-format"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

        # Test with field in request_args but not a comma-separated value
        # and not an operator value (line ~226)
        args = {"description": "simple value"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["description"]["value"], "simple value")

        # Test handling ValueError during operator parsing (lines ~242-264)
        with patch('service.common.helpers.parse_operator_value',
                   side_effect=ValueError("Invalid operator")):
            args = {"quantity": "~invalid~5"}
            with self.assertRaises(ValueError) as e:
                helpers.extract_item_filters(args)
            self.assertIn("Error parsing filter for quantity", str(e.exception))

    def test_process_operator_filters_all_cases(self):
        """Test _process_operator_filters with all cases (lines ~242-264)"""
        # Basic case
        args = {"quantity": "~lt~5"}
        filter_fields = ["quantity"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "lt")
        self.assertEqual(filters["quantity"]["value"], "5")

        # Case where field not in args
        args = {"price": "10"}
        filter_fields = ["quantity"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters, {})

        # Error case
        args = {"quantity": "~invalid~5"}
        filter_fields = ["quantity"]
        with patch('service.common.helpers.parse_operator_value',
                   side_effect=ValueError("Invalid operator")):
            with self.assertRaises(ValueError) as e:
                helpers._process_operator_filters(args, filter_fields)
            self.assertIn("Error parsing filter for quantity", str(e.exception))


if __name__ == "__main__":
    unittest.main()
