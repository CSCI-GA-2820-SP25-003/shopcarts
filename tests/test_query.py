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
        self.assertIn("error", data)
        # Use assertTrue with OR condition to handle both possible error messages
        self.assertTrue(
            "Min price larger than max price" in data["error"] or
            "min value cannot be greater" in data["error"]
        )

    def test_extract_filters_validation(self):
        """It should validate and handle edge cases in extract_item_filters"""
        # Test with malformed range where min > max
        response = self.client.get("/shopcarts/1?price_range=100,50")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)

        # Test with non-numeric values in range
        response = self.client.get("/shopcarts/1?price_range=abc,xyz")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
