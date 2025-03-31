import unittest
from service.common import helpers


class TestHelpers(unittest.TestCase):
    def test_extract_item_filters_valid_range(self):
        # Assume price_range extraction returns a dict with operator 'range'
        args = {"price_range": "10,50"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price"]["operator"], "range")
        self.assertEqual(filters["price"]["value"], ["10", "50"])

    def test_extract_item_filters_invalid_range(self):
        args = {"price_range": "100"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)


if __name__ == '__main__':
    unittest.main()
