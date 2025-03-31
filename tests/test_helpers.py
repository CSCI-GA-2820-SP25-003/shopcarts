"""Unit tests for helper functions in the Shopcart service."""

import unittest
from unittest.mock import patch
from flask import Flask
from service.common import helpers


# Create a dummy Shopcart class for testing cart functions
class DummyShopcart:
    """Mock Shopcart class for testing cart-related helper functions."""

    def __init__(self, user_id, item_id, quantity):
        """Initialize the mock Shopcart with required attributes."""
        self.user_id = user_id
        self.item_id = item_id
        self.quantity = quantity

    def update(self):
        """Mock update method."""
        pass

    def delete(self):
        """Mock delete method."""
        pass


class TestHelpersBase(unittest.TestCase):
    """Base test case class for helper functions with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()


class TestExtractItemFilters(TestHelpersBase):
    """Test cases for extract_item_filters function."""

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

    def test_extract_item_filters_direct_value(self):
        """Test extract_item_filters with a direct value (line 226)."""
        args = {"description": "Test Description"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["description"]["value"], "Test Description")

        args = {"description": "Test Description", "user_id": "123"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["user_id"]["operator"], "eq")

    def test_extract_item_filters_error_handling(self):
        """Test extract_item_filters with error handling for parse_operator_value (lines 242-264)."""
        with patch('service.common.helpers.parse_operator_value') as mock_parse:
            mock_parse.side_effect = ValueError("Test error from parse_operator_value")
            args = {"quantity": "~invalid~5"}
            with self.assertRaises(ValueError) as cm:
                helpers.extract_item_filters(args)
            self.assertIn("Error parsing filter for quantity", str(cm.exception))

    def test_extract_item_filters_all_types(self):
        """Test extract_item_filters with all possible input types (lines 269-286)."""
        for field in ["user_id", "quantity", "price", "created_at", "last_updated", "description", "item_id"]:
            range_key = f"{field}_range"
            args = {range_key: "1,10"}
            filters = helpers.extract_item_filters(args)
            self.assertEqual(filters[field]["operator"], "range")
            self.assertEqual(filters[field]["value"], ["1", "10"])

            args = {range_key: "invalid format"}
            with self.assertRaises(ValueError) as cm:
                helpers.extract_item_filters(args)
            self.assertIn(f"Invalid range format for {range_key}", str(cm.exception))

    def test_extract_item_filters_range_formats(self):
        """Test extract_item_filters with different range formats."""
        args = {"quantity_range": "5 , 10"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "range")
        self.assertEqual(filters["quantity"]["value"], ["5", "10"])

        args = {"quantity_range": ","}  # This now produces empty strings, triggering error
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    def test_combining_all_filter_types(self):
        """Test extract_item_filters with a combination of all filter types."""
        args = {
            "min-price": "10",
            "max-price": "100",
            "user_id": "123",
            "quantity": "~gt~5",
            "price_range": "20,50",
            "item_id": "1,2,3",
            "description": "Test Description"
        }
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price_min"], 10.0)
        self.assertEqual(filters["price_max"], 100.0)
        self.assertEqual(filters["user_id"]["operator"], "eq")
        self.assertEqual(filters["user_id"]["value"], "123")
        self.assertEqual(filters["quantity"]["operator"], "gt")
        self.assertEqual(filters["quantity"]["value"], "5")
        self.assertEqual(filters["price"]["operator"], "range")
        self.assertEqual(filters["price"]["value"], ["20", "50"])
        self.assertEqual(filters["item_id"]["operator"], "in")
        self.assertEqual(filters["item_id"]["value"], ["1", "2", "3"])
        self.assertEqual(filters["description"]["operator"], "eq")
        self.assertEqual(filters["description"]["value"], "Test Description")

    def test_extract_item_filters_uncovered_cases(self):
        """Test extract_item_filters with cases covering lines ~269-286."""
        args = {"quantity_range": "5,10"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "range")
        self.assertEqual(filters["quantity"]["value"], ["5", "10"])

        args = {"item_id": "50"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["item_id"]["operator"], "eq")
        self.assertEqual(filters["item_id"]["value"], "50")

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
        self.assertEqual(filters["price_min"], 5.0)
        self.assertEqual(filters["price_max"], 100.0)

    def test_extract_item_filters_range_edge_cases(self):
        """Test extract_item_filters range handling edge cases (lines 269-286)."""
        args = {"price_range": "10,50", "price": "25.99"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price"]["operator"], "range")
        args = {"price_range": "  ,  "}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)


class TestParseOperatorValue(TestHelpersBase):
    """Test cases for parse_operator_value function."""

    def test_parse_operator_value_eq(self):
        """Test parse_operator_value with equality operator."""
        result = helpers.parse_operator_value("eq:100")
        self.assertEqual(result, ("eq", "eq:100"))

    def test_parse_operator_value_lt(self):
        """Test parse_operator_value with lt operator."""
        result = helpers.parse_operator_value("~lt~10")
        self.assertEqual(result, ("lt", "10"))

    def test_parse_operator_value_lte(self):
        """Test parse_operator_value with lte operator."""
        result = helpers.parse_operator_value("~lte~20")
        self.assertEqual(result, ("lte", "20"))

    def test_parse_operator_value_gt(self):
        """Test parse_operator_value with gt operator."""
        result = helpers.parse_operator_value("~gt~30")
        self.assertEqual(result, ("gt", "30"))

    def test_parse_operator_value_gte(self):
        """Test parse_operator_value with gte operator."""
        result = helpers.parse_operator_value("~gte~40")
        self.assertEqual(result, ("gte", "40"))

    def test_parse_operator_value_wrapped(self):
        """Test parse_operator_value for wrapped operator syntax."""
        result = helpers.parse_operator_value("~gt~50")
        self.assertEqual(result, ("gt", "50"))

    def test_parse_operator_value_no_operator(self):
        """Test parse_operator_value when no operator is specified (defaults to 'eq')."""
        result = helpers.parse_operator_value("200")
        self.assertEqual(result, ("eq", "200"))

    def test_parse_operator_value_invalid(self):
        """Test that parse_operator_value raises ValueError on invalid format."""
        with self.assertRaises(ValueError):
            helpers.parse_operator_value("~invalid~3")

    def test_parse_operator_with_no_splits(self):
        """Test parse_operator_value with partial tilde format."""
        with self.assertRaises(ValueError) as context:
            helpers.parse_operator_value("~incomplete")
        self.assertIn("Invalid operator format", str(context.exception))

    def test_parse_operator_value_with_nested_tildes(self):
        """Test parse_operator_value with value containing tildes."""
        result = helpers.parse_operator_value("~gt~50~extra")
        self.assertEqual(result, ("gt", "50~extra"))

    def test_direct_function_call_to_parse_operator_value(self):
        """Test calling the parse_operator_value function directly with nested tildes."""
        self.assertEqual(helpers.parse_operator_value("~gt~10~with~tildes"), ("gt", "10~with~tildes"))


class TestValidateRequestData(TestHelpersBase):
    """Test cases for validate_request_data function."""

    def test_validate_request_data_error_cases(self):
        """Test validate_request_data with various error cases."""
        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({"quantity": "5", "name": "Test Product"})
        self.assertIn("'product_id'", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({"product_id": "123", "price": "not-a-price"})
        self.assertIn("Invalid input", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            helpers.validate_request_data({"product_id": "123", "quantity": "abc"})
        self.assertIn("Invalid input", str(cm.exception))

    def test_validate_request_data_noninteger_values(self):
        """Test validate_request_data with non-integer values."""
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "not-a-number",
                "name": "Test",
                "price": "10.0"
            })
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "5",
                "name": "Test",
                "price": "10.0",
                "stock": "invalid"
            })
        with self.assertRaises(ValueError):
            helpers.validate_request_data({
                "product_id": "123",
                "quantity": "5",
                "name": "Test",
                "price": "10.0",
                "purchase_limit": "invalid"
            })


class TestProcessOperatorFilters(TestHelpersBase):
    """Test cases for _process_operator_filters function."""

    def test_process_operator_filters_all_branches(self):
        """Test _process_operator_filters through all branches."""
        args = {"quantity": "5", "price": "10.99"}
        filter_fields = ["quantity", "price", "user_id"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(len(filters), 2)
        self.assertEqual(filters["quantity"]["operator"], "eq")
        self.assertEqual(filters["price"]["operator"], "eq")
        self.assertNotIn("user_id", filters)
        with patch('service.common.helpers.parse_operator_value') as mock_parse:
            mock_parse.side_effect = ValueError("Test error")
            with self.assertRaises(ValueError) as cm:
                helpers._process_operator_filters({"quantity": "5"}, ["quantity"])
            self.assertIn("Error parsing filter for quantity", str(cm.exception))

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
        self.assertNotIn("unknown", filters)
        self.assertNotIn("user_id", filters)

    def test_process_operator_filters_all_cases(self):
        """Test _process_operator_filters with all possible cases."""
        args = {"quantity": "~lt~5"}
        filter_fields = ["quantity"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "lt")
        self.assertEqual(filters["quantity"]["value"], "5")
        args = {"price": "10"}
        filter_fields = ["quantity"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters, {})

    def test_process_operator_filters_with_each_operator(self):
        """Test _process_operator_filters with each operator type."""
        filter_fields = ["quantity"]
        args = {"quantity": "~lt~5"}
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "lt")
        args = {"quantity": "~lte~10"}
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "lte")
        args = {"quantity": "~gt~15"}
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "gt")
        args = {"quantity": "~gte~20"}
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "gte")
        args = {"quantity": "25"}
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["quantity"]["operator"], "eq")

    def test_process_operator_filters_with_complex_value(self):
        """Test _process_operator_filters with a complex value containing special characters."""
        args = {"description": "Special~characters:with,commas"}
        filter_fields = ["description"]
        filters = helpers._process_operator_filters(args, filter_fields)
        self.assertEqual(filters["description"]["value"], "Special~characters:with,commas")


class TestPriceParameters(TestHelpersBase):
    """Test cases for price parameter helper functions."""

    def test_validate_price_parameter(self):
        """Test _validate_price_parameter with various inputs."""
        filters = {}
        args = {"min-price": "10"}
        filters = helpers._validate_price_parameter(args, "min-price", filters, "price_min")
        self.assertEqual(filters["price_min"], 10.0)
        args_invalid = {"min-price": "-5"}
        with self.assertRaises(ValueError):
            helpers._validate_price_parameter(args_invalid, "min-price", {}, "price_min")
        args_invalid = {"min-price": "abc"}
        with self.assertRaises(ValueError):
            helpers._validate_price_parameter(args_invalid, "min-price", {}, "price_min")

    def test_validate_price_range_valid(self):
        """Test _validate_price_range with a valid price range."""
        filters = {"price_min": 10.0, "price_max": 50.0}
        new_filters = helpers._validate_price_range(filters)
        self.assertEqual(new_filters, filters)

    def test_validate_price_range_invalid(self):
        """Test _validate_price_range with an invalid price range."""
        filters = {"price_min": 60.0, "price_max": 50.0}
        with self.assertRaises(ValueError) as context:
            helpers._validate_price_range(filters)
        self.assertIn("cannot be greater than", str(context.exception))


if __name__ == '__main__':
    unittest.main()
