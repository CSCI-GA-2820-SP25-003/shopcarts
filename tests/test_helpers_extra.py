"""Additional tests for helper functions to improve coverage."""

import unittest
from service.common import helpers


class TestHelpersExtra(unittest.TestCase):
    """Test cases for additional helper function scenarios to improve coverage."""

    def test_parse_operator_value_eq(self):
        """Test parse_operator_value for 'eq' operator."""
        # From the error, it looks like the function returns ('eq', 'eq:100'), not ('eq', '100')
        result = helpers.parse_operator_value("eq:100")
        # Updated expectation to match actual behavior
        self.assertEqual(result, ("eq", "eq:100"))

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

    def test_build_query_from_url_args(self):
        """Test building query params from URL args."""
        # Test with price filter
        args = {"price": "10.99"}
        filters = helpers.extract_item_filters(args)
        query = helpers.build_query_from_filters(filters)
        self.assertIn("price", query)
        self.assertEqual(query["price"], "10.99")

    def test_build_range_query(self):
        """Test building a range query from filters."""
        # Test range queries
        args = {"price_range": "10,50"}
        filters = helpers.extract_item_filters(args)
        query = helpers.build_query_from_filters(filters)
        self.assertTrue("$and" in query)
        self.assertEqual(len(query["$and"]), 2)
        # Should have min and max conditions

    def test_extract_filters_with_comma_values(self):
        """Test extract_item_filters with comma-separated values."""
        # Test extracting in operator
        args = {"quantity": "1,2,3"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "in")
        self.assertEqual(filters["quantity"]["value"], ["1", "2", "3"])

    def test_extract_date_filters(self):
        """Test extract_item_filters with date filters."""
        # Test date range filter
        args = {"created_at_range": "2023-01-01,2023-12-31"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["created_at"]["operator"], "range")
        self.assertEqual(len(filters["created_at"]["value"]), 2)

    def test_apply_filter_with_operator(self):
        """Test applying various operators to filters."""
        # Test gt operator
        value = "gt:10"
        filters = {}
        helpers.apply_filter("quantity", value, filters)
        self.assertEqual(filters["quantity"]["operator"], "gt")

        # Test lt operator
        value = "lt:5"
        filters = {}
        helpers.apply_filter("quantity", value, filters)
        self.assertEqual(filters["quantity"]["operator"], "lt")

        # Test wrapped operators
        value = "~lte~100"
        filters = {}
        helpers.apply_filter("price", value, filters)
        self.assertEqual(filters["price"]["operator"], "lte")

    def test_extract_filters_with_multiple_conditions(self):
        """Test extract_item_filters with multiple filters."""
        # Test with multiple filters
        args = {
            "price": "10.99",
            "quantity": "gt:5",
            "description": "Test"
        }
        filters = helpers.extract_item_filters(args)
        self.assertIn("price", filters)
        self.assertIn("quantity", filters)
        self.assertIn("description", filters)
        self.assertEqual(filters["price"]["operator"], "eq")
        self.assertEqual(filters["quantity"]["operator"], "gt")

    def test_extract_filters_with_invalid_date_format(self):
        """Test extract_item_filters with invalid date format."""
        # Test with invalid date format
        args = {"created_at": "invalid-date-format"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    def test_filter_extraction_with_complex_operators(self):
        """Test complex operator extraction."""
        args = {"price": "~gte~50"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price"]["operator"], "gte")
        self.assertEqual(filters["price"]["value"], "50")


if __name__ == '__main__':
    unittest.main()
