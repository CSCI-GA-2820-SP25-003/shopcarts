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
from datetime import datetime, timedelta, timezone
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

    def test_get_shopcarts_with_price_range(self):
        """It should return items based on price range filter"""
        self._populate_shopcarts(count=2, price=15.0)
        self._populate_shopcarts(count=1, price=45.0)
        self._populate_shopcarts(count=1, price=55.0)  # This should NOT be included

        url = "/shopcarts?price_range=10,50"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        invalid_items = [
            item
            for shopcart in data
            for item in shopcart["items"]
            if not (10 <= item["price"] <= 50)
        ]

        self.assertEqual(
            len(invalid_items), 0, f"Found items outside price range: {invalid_items}"
        )

    def test_get_shopcarts_with_extreme_and_partial_values(self):
        """It should handle extreme values and partial filters correctly"""

        self._populate_shopcarts(count=1, price=12.0)
        self._populate_shopcarts(count=1, price=1200.0)

        url = "/shopcarts?price_range=1000,2000"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["items"]), 1)

        url = "/shopcarts?price_range=10,999999"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        # Expect at least 2 items (12.0 and 1200.0 are valid)
        self.assertGreater(len(data), 0)

    def test_get_shopcarts_with_attribute_filters(self):
        """It should return items based on attribute filters"""

        self._populate_shopcarts(count=1, user_id=1, price=20.0, quantity=2)
        self._populate_shopcarts(count=1, user_id=2, price=45.0, quantity=4)
        self._populate_shopcarts(count=1, user_id=3, price=60.0, quantity=6)

        url = "/shopcarts?user_id=1"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["items"]), 1)

        url = "/shopcarts?price=~gt~40"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        self.assertEqual(len(data), 2)

        url = "/shopcarts?quantity=~lte~4"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        self.assertEqual(len(data), 2)

        url = "/shopcarts?user_id=2&price=~gt~30"

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        self.assertEqual(len(data), 1)

    def test_list_shopcarts_with_qty_range(self):
        """It should list shopcarts within a quantity range"""

        # Create 2 carts inside range, and 1 outside
        self._populate_shopcarts(count=2, quantity=15)
        self._populate_shopcarts(count=1, quantity=30)

        resp = self.client.get("/shopcarts?quantity_range=10,20")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)

        self.assertEqual(len(expanded_data), 2)
        for item in expanded_data:
            self.assertGreaterEqual(item["quantity"], 10)
            self.assertLessEqual(item["quantity"], 20)

    def test_list_shopcarts_with_date_range(self):
        """It should list shopcarts within a created_at and last_updated date range"""

        before_creation = datetime.now(timezone.utc) - timedelta(minutes=1)
        self._populate_shopcarts(count=1)
        after_creation = datetime.now(timezone.utc) + timedelta(days=2)

        range_start = (before_creation - timedelta(days=1)).strftime("%Y-%m-%d")
        range_end = (after_creation + timedelta(days=1)).strftime("%Y-%m-%d")

        resp = self.client.get(f"/shopcarts?created_at_range={range_start},{range_end}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)

        self.assertEqual(len(expanded_data), 1)
        created_at = datetime.fromisoformat(expanded_data[0]["created_at"])
        created_at = created_at.replace(tzinfo=timezone.utc)
        self.assertGreaterEqual(created_at, before_creation)
        self.assertLessEqual(created_at, after_creation)

        # For logic here, it's hard to manually change last_updated (automatically updated), since we only added a product
        # last_updated = created_at time, so we can check before_creation and after_creation for last updated
        last_updated = datetime.fromisoformat(expanded_data[0]["last_updated"])
        last_updated = created_at.replace(tzinfo=timezone.utc)
        self.assertGreaterEqual(last_updated, before_creation)
        self.assertLessEqual(last_updated, after_creation)

    def test_list_shopcarts_combined_filters(self):
        """It should list shopcarts matching multiple filters"""

        self._populate_shopcarts(count=2, price=75.0, quantity=25)
        self._populate_shopcarts(count=1, price=200.0, quantity=100)

        resp = self.client.get("/shopcarts?price_range=70,80&quantity_range=20,30")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)

        self.assertEqual(len(expanded_data), 2)
        for item in expanded_data:
            self.assertGreaterEqual(item["price"], 70.0)
            self.assertLessEqual(item["price"], 80.0)
            self.assertGreaterEqual(item["quantity"], 20)
            self.assertLessEqual(item["quantity"], 30)

    def test_list_shopcarts_with_invalid_range_filters(self):
        """It should return 400 for malformed or invalid range filters"""

        # Only one value (triggers: len(parts) != 2)
        resp = self.client.get("/shopcarts?price_range=100")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("expected start,end", data["error"])

        # Bad type (triggers: cast_func fails → ValueError)
        resp = self.client.get("/shopcarts?quantity_range=abc,10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("Invalid value for quantity", data["error"])

        # Reversed range (triggers: min > max check)
        resp = self.client.get("/shopcarts?user_id_range=10,2")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("min value cannot be greater", data["error"])

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
        resp = self.client.get("/shopcarts/1?quantity_range=10,20")
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
        resp = self.client.get("/shopcarts/1?price_range=40,60")
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
        resp = self.client.get("/shopcarts/1?quantity_range=10,30&price_range=70,80")
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
        resp = self.client.get("/shopcarts/1?price_range=40")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "Invalid range format for price_range: expected start,end", data["error"]
        )

        # Also test for quantity
        resp = self.client.get("/shopcarts/1?quantity_range=10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "Invalid range format for quantity_range: expected start,end", data["error"]
        )

    def test_apply_price_conflict_with_min_max(self):
        """It should return 400 if both price and min-price/max-price are used."""
        self._populate_shopcarts(count=1, user_id=1, price=50.00)

        resp = self.client.get("/shopcarts/1?price=~gte~40&min-price=30")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "Cannot use both 'price' or 'price_range' and 'min-price'/'max-price'",
            data["error"],
        )

    def test_invalid_min_max_price_values(self):
        """It should return 400 for invalid min-price or max-price values."""
        resp = self.client.get("/shopcarts/1?min-price=cheap")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)

        resp = self.client.get("/shopcarts/1?max-price=expensive")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_min_max_price_filter_on_shopcarts(self):
        """It should filter shopcarts by min-price and max-price, with and without user_id"""

        # Create matching and non-matching items
        self._populate_shopcarts(count=2, user_id=1, price=75.0)
        self._populate_shopcarts(count=2, user_id=1, price=85.0)
        self._populate_shopcarts(count=2, user_id=1, price=65.0)

        # Test: /shopcarts/1 (with user_id)
        resp = self.client.get("/shopcarts/1?min-price=70&max-price=80")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        items = data[0]["items"]

        self.assertEqual(len(items), 2)
        for item in items:
            self.assertGreaterEqual(item["price"], 70.0)
            self.assertLessEqual(item["price"], 80.0)

        # Test: /shopcarts (without user_id)
        resp = self.client.get("/shopcarts?min-price=70&max-price=80")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        all_items = []
        for cart in data:
            all_items.extend(cart["items"])

        self.assertEqual(len(all_items), 2)
        for item in all_items:
            self.assertGreaterEqual(item["price"], 70.0)
            self.assertLessEqual(item["price"], 80.0)
