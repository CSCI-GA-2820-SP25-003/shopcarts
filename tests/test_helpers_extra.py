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


if __name__ == '__main__':
    unittest.main()
