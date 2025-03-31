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
from datetime import datetime, timezone, timedelta
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

    def test_list_shopcarts_with_price_range(self):
        """It should list shopcarts within a price range"""

        # Create 2 entries with price in range
        self._populate_shopcarts(count=2, price=50.00)
        # Create 1 entry with price outside range
        self._populate_shopcarts(count=1, price=80.00)

        resp = self.client.get("/shopcarts?range_price=40,60")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 2)
        for item in expanded_data:
            self.assertGreaterEqual(item["price"], 40.0)
            self.assertLessEqual(item["price"], 60.0)

    def test_list_shopcarts_with_qty_range(self):
        """It should list shopcarts within a quantity range"""

        # Create 2 carts inside range, and 1 outside
        self._populate_shopcarts(count=2, quantity=15)
        self._populate_shopcarts(count=1, quantity=30)

        resp = self.client.get("/shopcarts?range_qty=10,20")
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
        after_creation = datetime.now(timezone.utc) + timedelta(minutes=1)

        range_start = (before_creation - timedelta(days=1)).strftime("%Y-%m-%d")
        range_end = (after_creation + timedelta(days=1)).strftime("%Y-%m-%d")

        resp = self.client.get(f"/shopcarts?range_created_at={range_start},{range_end}")
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

        resp = self.client.get("/shopcarts?range_price=70,80&range_qty=20,30")
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

    def test_list_shopcarts_with_bad_range(self):
        """It should return 400 when only one value is provided for the range"""

        self._populate_shopcarts(count=2, price=50.00)

        resp = self.client.get("/shopcarts?range_price=40")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("range_price must have two comma-separated values", data["error"])

        resp = self.client.get("/shopcarts?range_qty=10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("range_qty must have two comma-separated values", data["error"])

        resp = self.client.get("/shopcarts?range_created_at=01-01-2020")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "range_created_at must have two comma-separated values", data["error"]
        )

    def test_list_shopcarts_with_max_min_price(self):
        """It should list shopcarts within a price max and min"""

        # Create 2 entries with price in range
        self._populate_shopcarts(count=2, price=50.00)
        # Create 1 entry with price outside range
        self._populate_shopcarts(count=1, price=80.00)
        # Check max
        resp = self.client.get("/shopcarts?max-price=60")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 2)
        for item in expanded_data:
            self.assertLessEqual(item["price"], 60.0)
        # Check min
        resp = self.client.get("/shopcarts?min-price=70")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 1)
        for item in expanded_data:
            self.assertGreaterEqual(item["price"], 70.0)

        # Check range:
        resp = self.client.get("/shopcarts?max-price=70&min-price=50")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 2)
        for item in expanded_data:
            self.assertLessEqual(item["price"], 70.0)
            self.assertGreaterEqual(item["price"], 50.0)

    def test_list_shopcarts_with_bad_max_min_price(self):
        """It should return errors with bad max and min price"""

        # Create 2 entries with price in range
        self._populate_shopcarts(count=2, price=50.00)
        # Create 1 entry with price outside range
        self._populate_shopcarts(count=1, price=80.00)

        resp = self.client.get("/shopcarts?max-price=70&range_price=2,10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "Passed in both range_price and max_price/min_price query", data["error"]
        )

        resp = self.client.get("/shopcarts?min-price=70&range_price=2,10")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn(
            "Passed in both range_price and max_price/min_price query", data["error"]
        )

        resp = self.client.get("/shopcarts?min-price=70&max-price=20")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
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
