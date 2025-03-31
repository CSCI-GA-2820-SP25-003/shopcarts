"""Unit tests for helper functions in the Shopcart service."""

import unittest
from unittest.mock import patch
from service.common import helpers


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions in service.common.helpers."""

    def test_extract_item_filters_valid_range(self):
        """Test that extract_item_filters returns correct output for a valid price range."""
        args = {"price_range": "10,50"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price"]["operator"], "range")
        self.assertEqual(filters["price"]["value"], ["10", "50"])

    def test_extract_item_filters_invalid_range(self):
        """Test that extract_item_filters raises ValueError for an invalid price range input."""
        args = {"price_range": "100"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    # Additional tests for improved coverage

    def test_validate_request_data_error_cases(self):
        """Test validate_request_data with various error cases (line 139, 156)."""
        # Missing required product_id
        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({
                "quantity": "5",
                "name": "Test Product"
            })
        self.assertIn("'product_id'", str(cm.exception))

        # Invalid price format
        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({
                "product_id": "123",
                "price": "not-a-price"
            })
        self.assertIn("Invalid input", str(cm.exception))

        # Invalid quantity format
        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "abc"
            })
        self.assertIn("Invalid input", str(cm.exception))

    def test_extract_item_filters_direct_value(self):
        """Test extract_item_filters with a direct value (line 226)."""
        # Test with a simple value that triggers line 226 (not a comma-separated or operator value)
        args = {"description": "Test Description"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["description"]["value"], "Test Description")

        # Multiple direct values
        args = {
            "description": "Test Description",
            "user_id": "123"
        }
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["user_id"]["operator"], "eq")

    def test_extract_item_filters_error_handling(self):
        """Test extract_item_filters with error handling for parse_operator_value (lines 242-264)."""
        # Test the error handling path by forcing parse_operator_value to throw an error
        with patch('service.common.helpers.parse_operator_value') as mock_parse:
            mock_parse.side_effect = ValueError("Test error from parse_operator_value")
            args = {"quantity": "~invalid~5"}
            with self.assertRaises(ValueError) as cm:
                helpers.extract_item_filters(args)
            self.assertIn("Error parsing filter for quantity", str(cm.exception))

    def test_process_operator_filters_all_branches(self):
        """Test _process_operator_filters through all branches (lines 242-264)."""
        # Test with fields both in args and filter_fields
        args = {"quantity": "5", "price": "10.99"}
        filter_fields = ["quantity", "price", "user_id"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(len(filters), 2)
        self.assertEqual(filters["quantity"]["operator"], "eq")
        self.assertEqual(filters["price"]["operator"], "eq")

        # Test with fields in filter_fields but not in args (should be skipped)
        self.assertNotIn("user_id", filters)

        # Test error condition by forcing parse_operator_value to throw
        with patch('service.common.helpers.parse_operator_value') as mock_parse:
            mock_parse.side_effect = ValueError("Test error")
            with self.assertRaises(ValueError) as cm:
                helpers._process_operator_filters({"quantity": "5"}, ["quantity"])
            self.assertIn("Error parsing filter for quantity", str(cm.exception))

    def test_extract_item_filters_all_types(self):
        """Test extract_item_filters with all possible input types (lines 269-286)."""
        # Test the range key path (lines 269-286)
        for field in ["user_id", "quantity", "price", "created_at", "last_updated", "description", "item_id"]:
            # Test valid range format
            range_key = f"{field}_range"
            args = {range_key: "1,10"}
            filters = helpers.extract_item_filters(args)
            self.assertEqual(filters[field]["operator"], "range")
            self.assertEqual(filters[field]["value"], ["1", "10"])

            # Test invalid range format
            args = {range_key: "invalid format"}
            with self.assertRaises(ValueError) as cm:
                helpers.extract_item_filters(args)
            self.assertIn(f"Invalid range format for {range_key}", str(cm.exception))

    def test_combining_all_filter_types(self):
        """Test extract_item_filters with a combination of all filter types."""
        # This test should exercise all paths through extract_item_filters
        args = {
            "min-price": "10",                   # Direct min price
            "max-price": "100",                  # Direct max price
            "user_id": "123",                    # Direct eq filter
            "quantity": "~gt~5",                 # Operator filter
            "price_range": "20,50",              # Range filter
            "item_id": "1,2,3",                  # Comma-separated (IN) filter
            "description": "Test Description"    # Simple eq filter
        }

        filters = helpers.extract_item_filters(args)

        # Check min/max price
        self.assertEqual(filters["price_min"], 10.0)
        self.assertEqual(filters["price_max"], 100.0)

        # Check direct filter
        self.assertEqual(filters["user_id"]["operator"], "eq")
        self.assertEqual(filters["user_id"]["value"], "123")

        # Check operator filter
        self.assertEqual(filters["quantity"]["operator"], "gt")
        self.assertEqual(filters["quantity"]["value"], "5")

        # Check range filter
        self.assertEqual(filters["price"]["operator"], "range")
        self.assertEqual(filters["price"]["value"], ["20", "50"])

        # Check IN filter
        self.assertEqual(filters["item_id"]["operator"], "in")
        self.assertEqual(filters["item_id"]["value"], ["1", "2", "3"])

        # Check simple eq filter
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["description"]["value"], "Test Description")


if __name__ == '__main__':
    unittest.main()
