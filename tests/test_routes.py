######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
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
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.common import status
from service.models import db, Shopcart
from .factories import ShopcartFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Shopcart).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class TestShopcartService(TestCase):
    """Test cases for the Shopcart Service"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Configure your test database here
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql+psycopg2://postgres:postgres@localhost:5432/testdb"
        )
        app.app_context().push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Shopcart).delete()  # Clean up any leftover data
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _populate_shopcarts(self, count=5, user_id=None):
        """Create and populate shopcarts in the database using ShopcartFactory"""
        shopcarts = []
        for _ in range(count):

            if user_id is not None:
                shopcart = ShopcartFactory(user_id=user_id)
            else:
                shopcart = ShopcartFactory()
            payload = {
                "item_id": shopcart.item_id,
                "description": shopcart.description,
                "price": float(shopcart.price),
                "quantity": shopcart.quantity,
            }
            response = self.client.post(f"/shopcart/{shopcart.user_id}", json=payload)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            shopcarts.append(shopcart)
        return shopcarts

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_add_item_creates_new_cart_entry(self):
        """It should create a new cart entry when none exists for the user."""
        user_id = 1
        payload = {
            "item_id": 101,
            "description": "Test Item",
            "price": 9.99,
            "quantity": 2,
        }
        response = self.client.post(f"/shopcart/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user_id"], user_id)
        self.assertEqual(data[0]["item_id"], payload["item_id"])
        self.assertEqual(data[0]["quantity"], payload["quantity"])
        self.assertAlmostEqual(data[0]["price"], payload["price"], places=2)

    def test_add_item_updates_existing_entry(self):
        """It should update the quantity if the cart entry already exists."""
        user_id = 1
        # First, add the item
        payload = {
            "item_id": 101,
            "description": "Test Item",
            "price": 9.99,
            "quantity": 2,
        }
        response = self.client.post(f"/shopcart/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Add the same item again
        payload2 = {
            "item_id": 101,
            "description": "Test Item",
            "price": 9.99,
            "quantity": 3,
        }
        response2 = self.client.post(f"/shopcart/{user_id}", json=payload2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data = response2.get_json()

        # The quantity should now be 2 + 3 = 5
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["quantity"], 5)
        self.assertAlmostEqual(data[0]["price"], payload["price"], places=2)

    def test_add_item_missing_fields(self):
        """It should return a 400 error if required fields are missing."""
        user_id = 1
        # Missing 'item_id'
        payload = {"description": "Test Item", "price": 9.99}
        response = self.client.post(f"/shopcart/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)

    def test_add_item_invalid_input(self):
        """It should return a 400 error if fields have invalid data types."""
        user_id = 1
        # Non-integer 'item_id'
        payload = {"item_id": "abc", "description": "Test Item", "price": 9.99}
        response = self.client.post(f"/shopcart/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)

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

            # Find the corresponding cart in the response
            response_cart = next(
                (cart for cart in data if cart["user_id"] == shopcart.user_id), None
            )
            self.assertIsNotNone(
                response_cart,
                f"Shopcart for user {shopcart.user_id} not found in response",
            )

            # Verify the cart has items
            self.assertIn("items", response_cart)
            self.assertIsInstance(response_cart["items"], list)

            # Find the matching item in the response items
            response_item = next(
                (
                    item
                    for item in response_cart["items"]
                    if item["item_id"] == shopcart.item_id
                ),
                None,
            )

            # Verify the item exists and has correct data
            self.assertIsNotNone(
                response_item,
                f"Item {shopcart.item_id} for user {shopcart.user_id} not found in response",
            )

            # Check all relevant fields match
            self.assertEqual(response_item["user_id"], shopcart.user_id)
            self.assertEqual(response_item["item_id"], shopcart.item_id)
            self.assertEqual(response_item["description"], shopcart.description)
            self.assertEqual(response_item["quantity"], shopcart.quantity)
            self.assertAlmostEqual(float(response_item["price"]), float(shopcart.price))

            # Verify the response contains timestamps
            self.assertIn("created_at", response_item)
            self.assertIn("last_updated", response_item)

    def test_list_empty_shopcarts(self):
        """It should return an empty list when no shopcarts exist"""
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data, [])

    def test_list_shopcarts_server_error(self):
        """It should handle server errors gracefully"""
        # Create some test data to make sure the database is working initially
        self._populate_shopcarts(1)

        # Mock the database query to raise an exception with a specific message
        with patch(
            "service.models.Shopcart.all", side_effect=Exception("Database error")
        ):
            resp = self.client.get("/shopcarts")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify the response contains an error message with the exact format
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

            # Additional check to verify the format matches the implementation
            expected_error = "Internal server error: Database error"
            self.assertEqual(data["error"], expected_error)

    def test_read_user_shopcart(self):
        """It should get the shopcarts"""
        shopcart_user_1 = self._populate_shopcarts(count=3, user_id=1)
        shopcart_user_2 = self._populate_shopcarts(count=1, user_id=2)

        # Get the list of all shopcarts
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Verify response structure
        self.assertIsInstance(data, list)
        expanded_data = []
        for shopcart in data:
            for item in shopcart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 4)

        # Verify that both user_id 1 and 2 were created in the shopcart
        user_ids = set([cart["user_id"] for cart in data])
        self.assertEqual(user_ids, {1, 2})

        # Grab shopcart for user_id = 1
        resp = self.client.get("/shopcarts/1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data = resp.get_json()

        # Verify that user_data only grabbed shopcarts for user_id 1
        self.assertIsInstance(user_data, list)
        self.assertEqual(set([cart["user_id"] for cart in user_data]), {1})
        self.assertEqual(len(user_data), 1)
        self.assertEqual(len(user_data[0]["items"]), 3)
        print(user_data)
        for shopcart in shopcart_user_1:
            print(shopcart)
            response_item = next(
                (
                    item
                    for cart in user_data
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

        # Validate for user 2

        resp = self.client.get("/shopcarts/2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data_2 = resp.get_json()

        # Verify user_data only has shopcarts for user_id 2
        self.assertIsInstance(user_data_2, list)
        self.assertEqual(set([cart["user_id"] for cart in user_data_2]), {2})
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

    def test_read_empty_user_shopcart(self):
        """It should return an empty list if a user does not have any items"""
        self._populate_shopcarts(count=3, user_id=1)
        resp = self.client.get("/shopcarts")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Verify response structure
        self.assertIsInstance(data, list)
        expanded_data = []
        for shopcart in data:
            for item in shopcart["items"]:
                expanded_data.append(item)
        self.assertEqual(len(expanded_data), 3)

        # Verify that both user_id 1 and 2 were created in the shopcart
        user_ids = set([cart["user_id"] for cart in data])
        self.assertEqual(user_ids, {1})

        # Grab shopcart for user_id = 2
        resp = self.client.get("/shopcarts/2")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        user_data = resp.get_json()

        # Verify that we get an empty list for user_id = 2
        self.assertEqual(user_data, [])

    def test_read_user_shopcart_server_error(self):
        """Read by user_id should handle server errors gracefully"""
        # Create some test data to make sure the database is working initially
        self._populate_shopcarts(count=1, user_id=1)

        # Mock the database query to raise an exception with a specific message
        with patch(
            "service.models.Shopcart.find_by_user_id",
            side_effect=Exception("Database error"),
        ):
            resp = self.client.get("/shopcarts/1")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify the response contains an error message with the exact format
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

            # Additional check to verify the format matches the implementation
            expected_error = "Internal server error: Database error"
            self.assertEqual(data["error"], expected_error)

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
        self.assertEqual(len(data), 3)

        # Verify each item exists in the response
        for shopcart in shopcart_items:
            item_found = False
            for item in data:
                if item["item_id"] == shopcart.item_id:
                    item_found = True
                    self.assertEqual(item["user_id"], shopcart.user_id)
                    self.assertEqual(item["description"], shopcart.description)
                    self.assertEqual(item["quantity"], shopcart.quantity)
                    self.assertAlmostEqual(float(item["price"]), float(shopcart.price))
                    self.assertIn("created_at", item)
                    self.assertIn("last_updated", item)
            self.assertTrue(
                item_found, f"Item {shopcart.item_id} not found in response"
            )

    def test_get_empty_user_shopcart_items(self):
        """It should return an empty list when a user has no items"""
        # Create test data for user 2 (to make sure DB works)
        self._populate_shopcarts(count=1, user_id=2)

        # Get items for user 1 (who has no items)
        resp = self.client.get("/shopcarts/1/items")

        # Check response
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data, [])

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

    def test_delete_shopcart_item(self):
        """It should delete a specific item from a user's shopping cart"""
        # Create a user with multiple items in their cart
        shopcarts = self._populate_shopcarts(count=3, user_id=1)
        item_to_delete = shopcarts[0]
        
        # Delete one item
        resp = self.client.delete(f"/shopcarts/1/items/{item_to_delete.item_id}")
        
        # Check the response contains the updated cart
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_cart = resp.get_json()
        self.assertEqual(len(updated_cart), 2)  # One less item now
        
        # Verify the deleted item is not in the response
        item_ids = [item["item_id"] for item in updated_cart]
        self.assertNotIn(item_to_delete.item_id, item_ids)

    def test_delete_shopcart_item_server_error(self):
        """It should handle server errors gracefully when deleting items"""
        # Create some test data to make sure the database is working initially
        shopcart = self._populate_shopcarts(count=1, user_id=1)[0]
        
        # Mock the database find method to raise an exception with a specific message
        with patch(
            "service.models.Shopcart.find", 
            side_effect=Exception("Database error")
        ):
            resp = self.client.delete(f"/shopcarts/1/items/{shopcart.item_id}")
            
            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify the response contains an error message with the exact format
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    def test_delete_nonexistent_item(self):
        """It should return a 404 error when trying to delete an item that doesn't exist"""
        # Create some items for a user
        self._populate_shopcarts(count=1, user_id=1)
        
        # Try to delete an item that doesn't exist
        resp = self.client.delete(f"/shopcarts/1/items/99999")
        
        # Verify response
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_delete_last_item(self):
        """It should leave an empty cart when deleting the last item"""
        # Create a user with only one item
        shopcart = self._populate_shopcarts(count=1, user_id=1)[0]
        
        # Delete the only item
        resp = self.client.delete(f"/shopcarts/1/items/{shopcart.item_id}")
        
        # Verify response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)
