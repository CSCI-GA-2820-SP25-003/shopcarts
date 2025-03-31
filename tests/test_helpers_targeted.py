"""Test file focusing on uncovered edge cases in helpers.py"""

import unittest
from unittest.mock import patch
from service.common import helpers


class TestHelpersSpecificEdgeCases(unittest.TestCase):
    """Test class targeting specific uncovered edge cases in helpers.py"""

    def test_parse_operator_with_no_splits(self):
        """Test parse_operator_value with partial tilde format."""
        with self.assertRaises(ValueError) as context:
            helpers.parse_operator_value("~incomplete")
        self.assertIn("Invalid operator format", str(context.exception))

    def test_process_operator_filters_multiple_fields(self):
        """Test _process_operator_filters with multiple fields."""
        args = {"quantity": "~lt~5", "price": "~gt~10", "unknown": "value"}
        filter_fields = ["quantity", "price", "user_id"]
        filters = helpers._process_operator_filters(args, filter_fields)

        self.assertEqual(len(filters), 2)
        self.assertEqual(filters["quantity"]["operator"], "lt")
        self.assertEqual(filters["quantity"]["value"], "5")
        self.assertEqual(filters["price"]["operator"], "gt")
        self.assertEqual(filters["price"]["value"], "10")
        # unknown field is not in filter_fields, so it's ignored
        self.assertNotIn("unknown", filters)
        # user_id is in filter_fields but not in args, so it's ignored
        self.assertNotIn("user_id", filters)

    def test_extract_item_filters_complex_mix(self):
        """Test extract_item_filters with a complex mix of filter types."""
        args = {
            "quantity": "10",
            "price_range": "10,50",
            "item_id": "1,2,3",
            "user_id": "~gt~100",
            "min-price": "5",
            "max-price": "100",
            "created_at_range": "2023-01-01,2023-12-31"
        }

        filters = helpers.extract_item_filters(args)

        # Check direct value with equality operator
        self.assertEqual(filters["quantity"]["operator"], "eq")
        self.assertEqual(filters["quantity"]["value"], "10")

        # Check range values
        self.assertEqual(filters["price"]["operator"], "range")
        self.assertEqual(filters["price"]["value"], ["10", "50"])

        # Check comma-separated values for "in" operator
        self.assertEqual(filters["item_id"]["operator"], "in")
        self.assertEqual(filters["item_id"]["value"], ["1", "2", "3"])

        # Check operator prefixed values
        self.assertEqual(filters["user_id"]["operator"], "gt")
        self.assertEqual(filters["user_id"]["value"], "100")

        # Check min/max price parameters
        self.assertEqual(filters["price_min"], 5.0)
        self.assertEqual(filters["price_max"], 100.0)

        # Check another range parameter
        self.assertEqual(filters["created_at"]["operator"], "range")
        self.assertEqual(filters["created_at"]["value"], ["2023-01-01", "2023-12-31"])

    def test_extract_item_filters_invalid_operator_handling(self):
        """Test extract_item_filters with invalid operator."""
        # Mock parse_operator_value to raise ValueError
        with patch('service.common.helpers.parse_operator_value') as mock_parse:
            mock_parse.side_effect = ValueError("Invalid operator")

            args = {"quantity": "~invalid~5"}
            with self.assertRaises(ValueError) as context:
                helpers.extract_item_filters(args)

            self.assertIn("Error parsing filter for quantity", str(context.exception))

    def test_validate_request_data_missing_product_id(self):
        """Test validate_request_data with missing product_id"""
        # This should cover line 139
        data = {
            "quantity": "2",
            "name": "Test",
            "price": "9.99"
        }
        with self.assertRaises(ValueError) as context:
            helpers.validate_request_data(data)
        self.assertIn("Invalid input: 'product_id'", str(context.exception))

    def test_validate_request_data_invalid_price(self):
        """Test validate_request_data with invalid price"""
        # This should cover line 156 (invalid price format)
        data = {
            "product_id": "123",
            "quantity": "2",
            "name": "Test",
            "price": "not-a-price"
        }
        with self.assertRaises(ValueError) as context:
            helpers.validate_request_data(data)
        self.assertIn("Invalid input", str(context.exception))

    def test_extract_item_filters_range_formats(self):
        """Test extract_item_filters with different range formats"""
        # Test range format with extra spaces
        args = {"quantity_range": "5 , 10"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "range")
        self.assertEqual(filters["quantity"]["value"], ["5", "10"])

        # Test with totally invalid range format
        args = {"quantity_range": "not-a-range"}
        with self.assertRaises(ValueError) as context:
            helpers.extract_item_filters(args)
        self.assertIn("Invalid range format", str(context.exception))


if __name__ == '__main__':
    unittest.main()
