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
from decimal import Decimal  # Move standard library import to the top
import json
from unittest.mock import patch
from service.common import status  # First-party imports come after standard library
from .test_routes import TestShopcartService  # Local imports come last

######################################################################
#  T E S T   C A S E S
######################################################################

# pylint: disable=too-many-public-methods


class TestShopcartGet(TestShopcartService):
    """Test cases for get operations"""

    ######################################################################
    #  T E S T   C A S E S  (existing endpoints)
    ######################################################################
    def test_root_endpoint(self):
        """It should return API data at the root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertIsNotNone(data)

        self.assertEqual(data["name"], "Shopcart REST API Service")
        self.assertEqual(data["version"], "1.0")

        # Validate paths exist
        expected_paths = {
            "/shopcarts": {
                "GET": "Lists all shopcarts grouped by user",
            },
            "/shopcarts/{user_id}": {
                "POST": "Adds an item to a user's shopcart or updates quantity if it already exists",
                "GET": "Retrieves the shopcart with metadata",
                "PUT": "Updates the entire shopcart",
                "DELETE": "Deletes the entire shopcart (all items)",
            },
            "/shopcarts/{user_id}/items": {
                "POST": "Adds a product to a user's shopcart or updates quantity",
                "GET": "Lists all items in the user's shopcart (without metadata)",
            },
            "/shopcarts/{user_id}/items/{item_id}": {
                "GET": "Retrieves a specific item from the user's shopcart",
                "PUT": "Updates a specific item in the shopcart",
                "DELETE": "Removes an item from the shopcart",
            },
        }

        self.assertIn("paths", data)
        self.assertEqual(data["paths"], expected_paths)

    def test_health_endpoint(self):
        """It should return health status"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "OK")

    def test_list_shopcarts(self):
        """It should list all shopcarts in the database"""
        # Create test data
        shopcarts = self._populate_shopcarts(20)
        # Get the list of all shopcarts
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        # Verify response structure
        self.assertIsInstance(data, list)
        # Verify each shopcart exists in the response
        user_ids = [cart["user_id"] for cart in data]
        for shopcart in shopcarts:
            self.assertIn(shopcart.user_id, user_ids)
            response_cart = next(
                (cart for cart in data if cart["user_id"] == shopcart.user_id), None
            )
            self.assertIsNotNone(
                response_cart,
                f"Shopcart for user {shopcart.user_id} not found in response",
            )
            self.assertIn("items", response_cart)
            self.assertIsInstance(response_cart["items"], list)
            response_item = next(
                (
                    item
                    for item in response_cart["items"]
                    if item["item_id"] == shopcart.item_id
                ),
                None,
            )
            self.assertIsNotNone(
                response_item,
                f"Item {shopcart.item_id} for user {shopcart.user_id} not found in response",
            )
            self.assertEqual(response_item["user_id"], shopcart.user_id)
            self.assertEqual(response_item["item_id"], shopcart.item_id)
            self.assertEqual(response_item["description"], shopcart.description)
            self.assertEqual(response_item["quantity"], shopcart.quantity)
            self.assertAlmostEqual(float(response_item["price"]), float(shopcart.price))
            self.assertIn("created_at", response_item)
            self.assertIn("last_updated", response_item)

    def test_list_empty_shopcarts(self):
        """It should return an empty list when no shopcarts exist"""
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data, [])

    def test_read_user_shopcart(self):
        """It should get the shopcarts"""
        shopcart_user_1 = self._populate_shopcarts(count=3, user_id=1)
        shopcart_user_2 = self._populate_shopcarts(count=1, user_id=2)
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 4)
        user_ids = {cart["user_id"] for cart in data}
        self.assertEqual(user_ids, {1, 2})

        # Grab shopcart for user_id = 1
        resp = self.client.get("/shopcarts/1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data = resp.get_json()
        self.assertIsInstance(user_data, list)
        self.assertEqual({cart["user_id"] for cart in user_data}, {1})
        self.assertEqual(len(user_data), 1)
        self.assertEqual(len(user_data[0]["items"]), 3)

        for shopcart in shopcart_user_1:

            response_item = next(
                (
                    item
                    for cart in user_data
                    for item in cart["items"]
                    if item["item_id"] == shopcart.item_id
                ),
                None,
            )
            self.assertIsNotNone(
                response_item,
                f"Item {shopcart.item_id} for user {shopcart.user_id} not found in response",
            )
            self.assertEqual(response_item["user_id"], shopcart.user_id)
            self.assertEqual(response_item["item_id"], shopcart.item_id)
            self.assertEqual(response_item["description"], shopcart.description)
            self.assertEqual(response_item["quantity"], shopcart.quantity)
            self.assertAlmostEqual(float(response_item["price"]), float(shopcart.price))
            self.assertIn("created_at", response_item)
            self.assertIn("last_updated", response_item)

        # Validate for user 2
        resp = self.client.get("/shopcarts/2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data_2 = resp.get_json()
        self.assertIsInstance(user_data_2, list)
        self.assertEqual({cart["user_id"] for cart in user_data_2}, {2})
        self.assertEqual(len(user_data_2), 1)
        self.assertEqual(len(user_data_2[0]["items"]), 1)
        for shopcart in shopcart_user_2:
            response_item = next(
                (
                    item
                    for cart in user_data_2
                    for item in cart["items"]
                    if item["item_id"] == shopcart.item_id
                ),
                None,
            )
            self.assertIsNotNone(
                response_item,
                f"Item {shopcart.item_id} for user {shopcart.user_id} not found in response",
            )
            self.assertEqual(response_item["user_id"], shopcart.user_id)
            self.assertEqual(response_item["item_id"], shopcart.item_id)
            self.assertEqual(response_item["description"], shopcart.description)
            self.assertEqual(response_item["quantity"], shopcart.quantity)
            self.assertAlmostEqual(float(response_item["price"]), float(shopcart.price))
            self.assertIn("created_at", response_item)
            self.assertIn("last_updated", response_item)

    def test_read_empty_user_shopcart(self):
        """It should return an empty list if a user does not have any items"""
        self._populate_shopcarts(count=3, user_id=1)
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        expanded_data = []
        for cart in data:
            for item in cart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 3)
        user_ids = {cart["user_id"] for cart in data}
        self.assertEqual(user_ids, {1})

        # Grab shopcart for user_id = 2
        resp = self.client.get("/shopcarts/2")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_user_shopcart_server_error(self):
        """Read by user_id should handle server errors gracefully"""
        self._populate_shopcarts(count=1, user_id=1)
        # Patch at the controller level to ensure the exception is triggered
        with patch(
            "service.controllers.get_controller.Shopcart.find_by_user_id_with_filter",
            side_effect=Exception("Database error"),
        ):
            resp = self.client.get("/shopcarts/1")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertIn("Database error", data["error"])

    def test_get_user_shopcart_items(self):
        """It should get all items in a user's shopcart"""
        # Create test data for user 1
        shopcart_items = self._populate_shopcarts(count=3, user_id=1)

        # Get items for user 1
        resp = self.client.get("/shopcarts/1/items")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Verify response structure and content
        self.assertIsInstance(data, list)
        expanded_data = []
        for shopcart in data:
            for item in shopcart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 3)

        # Verify each item exists in the response
        self.assertIsInstance(data, list)
        self.assertEqual({cart["user_id"] for cart in data}, {1})
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["items"]), 3)

        for shopcart in shopcart_items:
            response_item = next(
                (
                    item
                    for cart in data
                    for item in cart["items"]
                    if item["item_id"] == shopcart.item_id
                ),
                None,
            )

            # Ensure the item exists in the response
            self.assertIsNotNone(
                response_item,
                f"Item {shopcart.item_id} for user {shopcart.user_id} not found in response",
            )

            # Validate the details of the item match
            self.assertEqual(response_item["user_id"], shopcart.user_id)
            self.assertEqual(response_item["item_id"], shopcart.item_id)
            self.assertEqual(response_item["description"], shopcart.description)
            self.assertEqual(response_item["quantity"], shopcart.quantity)
            self.assertAlmostEqual(float(response_item["price"]), float(shopcart.price))

            # Ensure timestamps exist
            self.assertIn("created_at", response_item)
            self.assertIn("last_updated", response_item)

    def test_get_empty_user_shopcart_items(self):
        """It should return an 404 when a user has no items"""
        # Create test data for user 2 (to make sure DB works)
        self._populate_shopcarts(count=1, user_id=2)

        # Get items for user 1 (who has no items)
        resp = self.client.get("/shopcarts/1/items")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_user_shopcart_items_server_error(self):
        """It should handle server errors gracefully when getting items"""
        # Create some test data to make sure the database is working initially
        self._populate_shopcarts(count=1, user_id=1)

        # Mock the database query to raise an exception with a specific message
        with patch(
            "service.models.Shopcart.find_by_user_id",
            side_effect=Exception("Database error"),
        ):
            resp = self.client.get("/shopcarts/1/items")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify the response contains an error message with the exact format
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    ######################################################################
    #  Get Cart Item Testcase
    ######################################################################

    def test_get_cart_item(self):
        """It should get a specific item from a user's shopcart"""
        user_id = 1
        # Create test data
        shopcarts = self._populate_shopcarts(count=3, user_id=user_id)
        item_id = shopcarts[0].item_id

        # Get the specific item
        response = self.client.get(f"/shopcarts/{user_id}/items/{item_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the response data
        data = response.get_json()
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(data["item_id"], item_id)
        self.assertEqual(data["description"], shopcarts[0].description)
        self.assertEqual(data["quantity"], shopcarts[0].quantity)
        self.assertAlmostEqual(float(data["price"]), float(shopcarts[0].price))
        self.assertIn("created_at", data)
        self.assertIn("last_updated", data)

    def test_get_cart_item_not_found(self):
        """It should return 404 when trying to get a non-existent item from a shopcart"""
        user_id = 1
        # Create some items for the user (to ensure the user exists)
        self._populate_shopcarts(count=1, user_id=user_id)

        # Try to get a non-existent item
        non_existent_item_id = 9999
        response = self.client.get(f"/shopcarts/{user_id}/items/{non_existent_item_id}")

        # Verify it returns a 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn(f"Item {non_existent_item_id} not found", data["error"])

    def test_get_cart_item_non_existent_user(self):
        """It should return 404 when trying to get an item for a non-existent user"""
        # Try to get an item for a user that doesn't exist
        non_existent_user_id = 9999
        response = self.client.get(f"/shopcarts/{non_existent_user_id}/items/1")

        # Verify it returns a 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)

    def test_get_cart_item_server_error(self):
        """It should handle server errors gracefully when getting a specific item"""
        user_id = 1
        item_id = 1
        # Create some test data to make sure the database is working initially
        self._populate_shopcarts(count=1, user_id=user_id)

        # Mock the database query to raise an exception with a specific message
        with patch(
            "service.models.Shopcart.find", side_effect=Exception("Database error")
        ):
            response = self.client.get(f"/shopcarts/{user_id}/items/{item_id}")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            # Verify the response contains an error message
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    ######################################################################
    #  Test Cases for Price Filters
    ######################################################################

    def test_get_shopcart_with_max_price_filter(self):
        """It should filter items by maximum price"""
        # Create a user with multiple items at different price points
        user_id = 750
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("10.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("25.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("50.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("75.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("100.00"))

        # Test with max-price=50
        response = self.client.get(f"/shopcarts/{user_id}?max-price=50")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse response data
        data = response.get_json()
        self.assertEqual(len(data), 1)
        cart_items = data[0]["items"]

        # Verify only items <= 50.00 are returned (should be 3 items: 10, 25, 50)
        self.assertEqual(len(cart_items), 3)
        for item in cart_items:
            self.assertLessEqual(float(item["price"]), 50.00)

    def test_get_shopcart_with_min_price_filter(self):
        """It should filter items by minimum price"""
        # Create a user with multiple items at different price points
        user_id = 751
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("10.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("25.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("50.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("75.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("100.00"))

        # Test with min-price=50
        response = self.client.get(f"/shopcarts/{user_id}?min-price=50")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse response data
        data = response.get_json()
        self.assertEqual(len(data), 1)
        cart_items = data[0]["items"]

        # Verify only items >= 50.00 are returned (should be 3 items: 50, 75, 100)
        self.assertEqual(len(cart_items), 3)
        for item in cart_items:
            self.assertGreaterEqual(float(item["price"]), 50.00)

    def test_get_shopcart_with_price_range_filter(self):
        """It should filter items by both minimum and maximum price"""
        # Create a user with multiple items at different price points
        user_id = 752
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("10.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("25.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("50.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("75.00"))
        self._populate_shopcarts(count=1, user_id=user_id, price=Decimal("100.00"))

        # Test with min-price=25 and max-price=75
        response = self.client.get(f"/shopcarts/{user_id}?min-price=25&max-price=75")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse response data
        data = response.get_json()
        self.assertEqual(len(data), 1)
        cart_items = data[0]["items"]

        # Verify only items between 25.00 and 75.00 inclusive are returned (should be 3 items: 25, 50, 75)
        self.assertEqual(len(cart_items), 3)
        for item in cart_items:
            price = float(item["price"])
            self.assertGreaterEqual(price, 25.00)
            self.assertLessEqual(price, 75.00)

    def test_get_shopcart_with_invalid_price_range(self):
        """It should return an error when min-price > max-price"""
        user_id = 753
        self._populate_shopcarts(count=2, user_id=user_id)

        # Test with min-price=100 and max-price=50
        response = self.client.get(f"/shopcarts/{user_id}?min-price=100&max-price=50")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify error message
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("min-price", data["error"])
        self.assertIn("max-price", data["error"])

    def test_get_shopcart_with_invalid_price_format(self):
        """It should return an error when price parameters are not valid numbers"""
        user_id = 754
        self._populate_shopcarts(count=2, user_id=user_id)

        # Test with non-numeric min-price
        response = self.client.get(f"/shopcarts/{user_id}?min-price=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify error message
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid min-price format", data["error"])

    ######################################################################
    #  Test Cases for Error Handling
    ######################################################################

    def test_bad_request(self):
        """It should handle bad request errors"""
        # Send a request that will trigger a 400 Bad Request
        resp = self.app.post(
            "/shopcarts",
            json={"invalid": "data", "user_id": "not-an-integer"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Bad Request")

    def test_internal_server_error(self):
        """It should handle internal server errors"""
        # We'll mock a method to force a 500 error

        with patch("service.models.Shopcart.all", side_effect=Exception("Database error")):
            resp = self.app.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = json.loads(resp.data)
            self.assertIn("status", data)
            self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal Server Error")
