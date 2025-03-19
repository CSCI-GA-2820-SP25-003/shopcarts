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
from datetime import datetime, timedelta
from service.common import status
from service.models import Shopcart
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

        # ✅ Print the test request URL
        url = "/shopcarts?range_price=10,50"
        print(f"\n🔍 DEBUG: Sending request: {url}")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        print("\n🔍 DEBUG: Full Response from API:", data)

        # ✅ Ensure that only valid items are returned
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

        # ✅ Populate shopcarts with extreme price values
        self._populate_shopcarts(count=1, price=12.0)
        self._populate_shopcarts(count=1, price=1200.0)

        # ✅ Query with extreme values (should return only one item)
        url = "/shopcarts?range_price=1000,2000"
        print(f"\n🔍 DEBUG: Sending request: {url}")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        print("\n🔍 DEBUG: Full Response from API:", data)

        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["items"]), 1)

        url = "/shopcarts?range_price=10,999999"

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

    def test_find_by_ranges(self):
        """It should return items based on price and quantity filters, and validate date ranges automatically."""

        self._populate_shopcarts(count=1, price=15.0, quantity=2)
        self._populate_shopcarts(count=1, price=45.0, quantity=4)
        self._populate_shopcarts(count=1, price=55.0, quantity=6)

        before_filter = datetime.utcnow() - timedelta(minutes=1)
        after_filter = datetime.utcnow() + timedelta(minutes=1)

        filters = {
            "min_price": 10,
            "max_price": 50,  # Price Range: Should return first two items
            "min_qty": 1,
            "max_qty": 5,  # Quantity Range: Should exclude third item
            "min_date": before_filter,  # Start Date (just before population)
            "max_date": after_filter,  # End Date (just after population)
            "min_update": before_filter,  # Start Update Date
            "max_update": after_filter,  # End Update Date
        }

        results = Shopcart.find_by_ranges(filters)

        self.assertGreater(len(results), 0)  # Ensure some results
        self.assertEqual(len(results), 2)  # Should exclude the third item

        # Ensure all results are within the price and quantity range
        for item in results:
            self.assertTrue(10 <= item.price <= 50)
            self.assertTrue(1 <= item.quantity <= 5)

            # Convert stored timestamps to naive datetime for comparison
            created_at_naive = item.created_at.replace(tzinfo=None)
            last_updated_naive = item.last_updated.replace(tzinfo=None)

            # Ensure `created_at` and `last_updated` are within expected range
            self.assertTrue(before_filter <= created_at_naive <= after_filter)
            self.assertTrue(before_filter <= last_updated_naive <= after_filter)
