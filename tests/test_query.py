######################################################################
# Copyright 2016, 2024 John J.
# Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
TestYourResourceModel API Service Test Suite
"""

# pylint: disable=duplicate-code
from service.common import status
from .test_routes import TestShopcartService

######################################################################
#  T E S T   C A S E S
######################################################################


class TestQuery(TestShopcartService):
    """Test cases for query operations"""

    ######################################################################
    #  T E S T   C A S E S  (existing endpoints)

    def test_get_user_shopcart_with_filter(self):
        """It should filter shopcart items by equality"""
        # Create test data with multiple quantities
        user_id = 1
        self._populate_shopcarts(count=2, user_id=user_id, quantity=5)
        self._populate_shopcarts(count=1, user_id=user_id, quantity=10)

        # Get items with quantity=5
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=5")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Verify response structure and content
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user_id"], user_id)

        # Only items with quantity=5 should be returned
        items = data[0]["items"]
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item["quantity"], 5)

    def test_get_user_shopcart_with_operator_filter(self):
        """It should filter shopcart items using operators"""
        # Create test data with various quantities
        user_id = 1
        self._populate_shopcarts(count=1, user_id=user_id, quantity=5)
        self._populate_shopcarts(count=1, user_id=user_id, quantity=10)
        self._populate_shopcarts(count=1, user_id=user_id, quantity=15)

        # Get items with quantity less than 10
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~lt~10")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Only items with quantity < 10 should be returned
        items = data[0]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 5)

        # Test greater than operator
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~gt~10")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 15)

        # Test less than or equal to
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~lte~10")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]
        self.assertEqual(len(items), 2)
        quantities = [item["quantity"] for item in items]
        self.assertIn(5, quantities)
        self.assertIn(10, quantities)

    def test_get_user_shopcart_with_multiple_filters(self):
        """It should apply multiple filter conditions"""
        # Create test data with various prices and quantities
        user_id = 1
        self._populate_shopcarts(count=1, user_id=user_id, price=25.0, quantity=5)
        self._populate_shopcarts(count=1, user_id=user_id, price=50.0, quantity=10)
        self._populate_shopcarts(count=1, user_id=user_id, price=75.0, quantity=15)

        # Filter by both price and quantity
        resp = self.client.get(f"/shopcarts/{user_id}?price=~gt~30&quantity=~lt~15")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Only the item that matches both conditions should be returned
        items = data[0]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["price"], 50.0)
        self.assertEqual(items[0]["quantity"], 10)

    def test_get_user_shopcart_with_invalid_filter(self):
        """It should handle invalid filter values gracefully"""
        # Create some test data
        user_id = 1
        self._populate_shopcarts(count=1, user_id=user_id)

        # Test with invalid price format
        resp = self.client.get(f"/shopcarts/{user_id}?price=invalid")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid value for price", data["error"])

        # Test with invalid operator
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~invalid~10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Unsupported operator", data["error"])

        # Test with invalid date format
        resp = self.client.get(f"/shopcarts/{user_id}?created_at=01-01-2020")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid value for created_at", data["error"])

    def test_filter_with_gte_operator(self):
        """It should correctly handle greater than or equal to operator"""
        # Create test data
        user_id = 1

        # Create items with different quantities
        self._populate_shopcarts(count=1, user_id=user_id, quantity=5)
        self._populate_shopcarts(count=1, user_id=user_id, quantity=10)
        self._populate_shopcarts(count=1, user_id=user_id, quantity=15)

        # Test greater than or equal to operator with quantity
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~gte~10")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Only items with quantity >= 10 should be returned
        items = data[0]["items"]
        self.assertEqual(len(items), 2)

        # Verify returned quantities
        quantities = [item["quantity"] for item in items]
        self.assertIn(10, quantities)
        self.assertIn(15, quantities)
        self.assertNotIn(5, quantities)

        # Test with a boundary value
        resp = self.client.get(f"/shopcarts/{user_id}?quantity=~gte~5")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # All items should match (quantities 5, 10, 15)
        items = data[0]["items"]
        self.assertEqual(len(items), 3)

    def test_apply_range_filters_no_filters(self):
        """It should return all shopcart items when no range filters are provided."""
        # Populate shopcart for user 1
        self._populate_shopcarts(count=3, user_id=1, quantity=10, price=50.00)
        # Call without any range filters
        resp = self.client.get("/shopcarts/1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data[0]["items"]), 3)

    def test_apply_range_filters_qty(self):
        """It should filter shopcart items based on quantity range."""
        # Create 2 items with quantity in range (e.g. 15) and 1 outside (e.g. 30)
        self._populate_shopcarts(count=2, user_id=1, quantity=15)
        self._populate_shopcarts(count=1, user_id=1, quantity=30)
        # Use quantity range filter: only items with quantity between 10 and 20 should pass
        resp = self.client.get("/shopcarts/1?range_qty=10,20")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]
        # Only the two items with quantity 15 should be returned
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertGreaterEqual(item["quantity"], 10)
            self.assertLessEqual(item["quantity"], 20)

    def test_apply_range_filters_price(self):
        """It should filter shopcart items based on price range."""
        # Create 2 items with price in range (e.g. 45.00) and 1 outside (e.g. 80.00)
        self._populate_shopcarts(count=2, user_id=1, price=45.00)
        self._populate_shopcarts(count=1, user_id=1, price=80.00)
        # Use price range filter: only items with price between 40 and 60 should pass
        resp = self.client.get("/shopcarts/1?range_price=40,60")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]
        # Only the 2 items with price 45.00 should be returned
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertGreaterEqual(item["price"], 40.0)
            self.assertLessEqual(item["price"], 60.0)

    def test_apply_range_filters_combined(self):
        """It should filter shopcart items based on combined quantity and price ranges."""
        # Create 2 items with quantity 20 and price 75.0, and 1 item with quantity 100 and price 200.0
        self._populate_shopcarts(count=2, user_id=1, quantity=20, price=75.0)
        self._populate_shopcarts(count=1, user_id=1, quantity=100, price=200.0)
        # Use combined filters: quantity between 10 and 30 and price between 70 and 80
        resp = self.client.get("/shopcarts/1?range_qty=10,30&range_price=70,80")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]
        # Only the 2 items with quantity 20 and price 75.0 should pass both filters
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertGreaterEqual(item["quantity"], 10)
            self.assertLessEqual(item["quantity"], 30)
            self.assertGreaterEqual(item["price"], 70.0)
            self.assertLessEqual(item["price"], 80.0)

    def test_apply_range_filters_invalid(self):
        """It should return 400 if an invalid range filter is provided (e.g. only one value)."""
        # Create some shopcart items
        self._populate_shopcarts(count=2, user_id=1, price=50.00)
        # Send an invalid range filter with only one value for price
        resp = self.client.get("/shopcarts/1?range_price=40")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("range_price must have two comma-separated values", data["error"])

        # Also test for quantity
        resp = self.client.get("/shopcarts/1?range_qty=10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("range_qty must have two comma-separated values", data["error"])
