"""Additional tests for helper functions to improve coverage."""

import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from service.common import helpers, status


class TestParseOperatorValue(unittest.TestCase):
    """Test cases for the parse_operator_value function."""

    def test_parse_operator_value_eq(self):
        """Test parse_operator_value with equality operator"""
        # Special format "eq:100" should return (eq, eq:100) since it's not a wrapped format
        result = helpers.parse_operator_value("eq:100")
        self.assertEqual(result, ("eq", "eq:100"))

    def test_parse_operator_value_lt(self):
        """Test parse_operator_value with lt operator"""
        result = helpers.parse_operator_value("~lt~10")
        self.assertEqual(result, ("lt", "10"))

    def test_parse_operator_value_lte(self):
        """Test parse_operator_value with lte operator"""
        result = helpers.parse_operator_value("~lte~20")
        self.assertEqual(result, ("lte", "20"))

    def test_parse_operator_value_gt(self):
        """Test parse_operator_value with gt operator"""
        result = helpers.parse_operator_value("~gt~30")
        self.assertEqual(result, ("gt", "30"))

    def test_parse_operator_value_gte(self):
        """Test parse_operator_value with gte operator"""
        result = helpers.parse_operator_value("~gte~40")
        self.assertEqual(result, ("gte", "40"))

    def test_parse_operator_value_invalid_format(self):
        """Test parse_operator_value with invalid format"""
        with self.assertRaises(ValueError):
            helpers.parse_operator_value("~incomplete")

    def test_parse_operator_value_unsupported_operator(self):
        """Test parse_operator_value with unsupported operator"""
        with self.assertRaises(ValueError):
            helpers.parse_operator_value("~unknown~50")

    def test_parse_operator_value_with_nested_tildes(self):
        """Test parse_operator_value with value containing tildes"""
        result = helpers.parse_operator_value("~gt~50~extra")
        self.assertEqual(result, ("gt", "50~extra"))


class TestExtractItemFilters(unittest.TestCase):
    """Test cases for the extract_item_filters function."""

    def test_extract_item_filters_min_max_price(self):
        """Test extract_item_filters with min-price and max-price"""
        args = {"min-price": "10", "max-price": "50"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["price_min"], 10.0)
        self.assertEqual(filters["price_max"], 50.0)

    def test_extract_item_filters_invalid_price_range(self):
        """Test extract_item_filters with invalid price range"""
        args = {"min-price": "50", "max-price": "10"}  # min > max
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    def test_extract_item_filters_negative_price(self):
        """Test extract_item_filters with negative price"""
        args = {"min-price": "-10"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    def test_extract_item_filters_invalid_price_format(self):
        """Test extract_item_filters with invalid price format"""
        args = {"min-price": "abc"}
        with self.assertRaises(ValueError):
            helpers.extract_item_filters(args)

    def test_extract_item_filters_with_range_param(self):
        """Test extract_item_filters with range parameter"""
        args = {"quantity_range": "5,10"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["quantity"]["operator"], "range")
        self.assertEqual(filters["quantity"]["value"], ["5", "10"])

    def test_extract_item_filters_with_comma_values(self):
        """Test extract_item_filters with comma-separated values"""
        args = {"item_id": "1,2,3"}
        filters = helpers.extract_item_filters(args)
        self.assertEqual(filters["item_id"]["operator"], "in")
        self.assertEqual(filters["item_id"]["value"], ["1", "2", "3"])

    def test_extract_item_filters_with_all_filter_fields(self):
        """Test extract_item_filters with all filter fields"""
        args = {
            "user_id": "1",
            "quantity": "~gt~5",
            "price": "10.99",
            "created_at": "2023-01-01",
            "last_updated": "2023-12-31",
            "description": "Test",
            "item_id": "100"
        }
        filters = helpers.extract_item_filters(args)
        self.assertEqual(len(filters), 7)  # All 7 fields should be present
        self.assertEqual(filters["quantity"]["operator"], "gt")


class TestStockAndLimits(unittest.TestCase):
    """Test cases for validate_stock_and_limits function."""

    def test_validate_stock_and_limits_out_of_stock(self):
        """Test validate_stock_and_limits with out of stock"""
        response = helpers.validate_stock_and_limits(5, 0, None)
        self.assertIsNotNone(response)
        self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)

    def test_validate_stock_and_limits_exceeds_stock(self):
        """Test validate_stock_and_limits with quantity exceeding stock"""
        response = helpers.validate_stock_and_limits(10, 5, None)
        self.assertIsNotNone(response)
        self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)

    def test_validate_stock_and_limits_exceeds_purchase_limit(self):
        """Test validate_stock_and_limits with quantity exceeding purchase limit"""
        response = helpers.validate_stock_and_limits(10, None, 5)
        self.assertIsNotNone(response)
        self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)

    def test_validate_stock_and_limits_valid(self):
        """Test validate_stock_and_limits with valid inputs"""
        response = helpers.validate_stock_and_limits(5, 10, 10)
        self.assertIsNone(response)


class TestCartHelpers(unittest.TestCase):
    """Test cases for cart helper functions."""

    def setUp(self):
        """Set up for tests"""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    # Tests for update_or_create_cart_item function
    @patch('service.common.helpers.Shopcart.find')
    @patch('service.common.helpers.Shopcart.update')
    def test_update_or_create_cart_item_existing(self, mock_update, mock_find):
        """Test update_or_create_cart_item with existing item"""
        # Mock existing cart item
        mock_cart_item = MagicMock()
        mock_cart_item.quantity = 5
        mock_find.return_value = mock_cart_item

        # Mock find_by_user_id to return a list
        with patch('service.common.helpers.Shopcart.find_by_user_id', return_value=["item1"]):
            product_data = {
                "product_id": 1,
                "quantity": 3,
                "name": "Test Product",
                "price": 10.99,
                "stock": 10,
                "purchase_limit": 10
            }
            result = helpers.update_or_create_cart_item(1, product_data)
            self.assertEqual(result, ["item1"])
            self.assertEqual(mock_cart_item.quantity, 8)  # 5 + 3
            mock_update.assert_called_once()

    @patch('service.common.helpers.Shopcart.find')
    @patch('service.common.helpers.Shopcart.create')
    def test_update_or_create_cart_item_new(self, mock_create, mock_find):
        """Test update_or_create_cart_item with new item"""
        # Mock no existing cart item
        mock_find.return_value = None

        # Mock find_by_user_id to return a list
        with patch('service.common.helpers.Shopcart.find_by_user_id', return_value=["new_item"]):
            product_data = {
                "product_id": 1,
                "quantity": 3,
                "name": "Test Product",
                "price": 10.99,
                "stock": None,
                "purchase_limit": None
            }
            result = helpers.update_or_create_cart_item(1, product_data)
            self.assertEqual(result, ["new_item"])
            mock_create.assert_called_once()

    @patch('service.common.helpers.Shopcart.find')
    def test_update_or_create_cart_item_exceeds_limit(self, mock_find):
        """Test update_or_create_cart_item with quantity exceeding limits"""
        # Mock existing cart item with quantity that would exceed limits
        mock_cart_item = MagicMock()
        mock_cart_item.quantity = 8
        mock_find.return_value = mock_cart_item

        product_data = {
            "product_id": 1,
            "quantity": 3,
            "name": "Test Product",
            "price": 10.99,
            "stock": 10,  # Total would be 11 (8+3) which exceeds stock
            "purchase_limit": 15
        }

        with self.assertRaises(ValueError):
            helpers.update_or_create_cart_item(1, product_data)


class TestCartUpdateHelpers(unittest.TestCase):
    """Test cases for cart update helper functions."""

    # Tests for process_cart_updates function
    @patch('service.common.helpers.update_cart_item_helper')
    def test_process_cart_updates(self, mock_update_helper):
        """Test process_cart_updates with valid items"""
        items = [
            {"item_id": "1", "quantity": 5},
            {"item_id": "2", "quantity": 10}
        ]
        helpers.process_cart_updates(1, items)
        self.assertEqual(mock_update_helper.call_count, 2)

    def test_process_cart_updates_invalid_item(self):
        """Test process_cart_updates with invalid item (missing item_id)"""
        items = [{"quantity": 5}]  # Missing item_id
        with self.assertRaises(ValueError):
            helpers.process_cart_updates(1, items)

    def test_process_cart_updates_negative_quantity(self):
        """Test process_cart_updates with negative quantity"""
        items = [{"item_id": "1", "quantity": -5}]
        with self.assertRaises(ValueError):
            helpers.process_cart_updates(1, items)

    # Tests for update_cart_item_helper function
    @patch('service.common.helpers.Shopcart.find')
    @patch('service.common.helpers.Shopcart.delete')
    def test_update_cart_item_helper_zero_quantity(self, mock_delete, mock_find):
        """Test update_cart_item_helper with zero quantity (delete)"""
        # Mock existing cart item
        mock_cart_item = MagicMock()
        mock_find.return_value = mock_cart_item

        helpers.update_cart_item_helper(1, 100, 0)
        mock_delete.assert_called_once()

    @patch('service.common.helpers.Shopcart.find')
    @patch('service.common.helpers.Shopcart.update')
    def test_update_cart_item_helper_update_quantity(self, mock_update, mock_find):
        """Test update_cart_item_helper with non-zero quantity (update)"""
        # Mock existing cart item
        mock_cart_item = MagicMock()
        mock_find.return_value = mock_cart_item

        helpers.update_cart_item_helper(1, 100, 5)
        self.assertEqual(mock_cart_item.quantity, 5)
        mock_update.assert_called_once()

    @patch('service.common.helpers.Shopcart.find')
    def test_update_cart_item_helper_not_found(self, mock_find):
        """Test update_cart_item_helper with non-existent item"""
        # Mock no existing cart item
        mock_find.return_value = None

        with self.assertRaises(LookupError):
            helpers.update_cart_item_helper(1, 999, 5)


if __name__ == '__main__':
    unittest.main()
