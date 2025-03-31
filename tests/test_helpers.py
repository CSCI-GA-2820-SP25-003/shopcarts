"""Unit tests for helper functions in the Shopcart service."""

import unittest
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


if __name__ == '__main__':
    unittest.main()
