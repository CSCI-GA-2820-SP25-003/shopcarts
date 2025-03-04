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
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.common import status
from service.models import db, Shopcart
from .factories import ShopcartFactory, mock_product

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods


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
        app.logger.setLevel(logging.CRITICAL)
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
            response = self.client.post(f"/shopcarts/{shopcart.user_id}", json=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            shopcarts.append(shopcart)
        return shopcarts

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

    def test_add_item_creates_new_cart_entry(self):
        """It should create a new cart entry when none exists for the user."""
        user_id = 1
        payload = {
            "item_id": 101,
            "description": "Test Item",
            "price": 9.99,
            "quantity": 2,
        }
        response = self.client.post(f"/shopcarts/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_url = f"http://localhost/shopcarts/{user_id}"
        self.assertIn("Location", response.headers)
        self.assertEqual(response.headers["Location"], expected_url)

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
        response = self.client.post(f"/shopcarts/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_url = f"http://localhost/shopcarts/{user_id}"
        self.assertIn("Location", response.headers)
        self.assertEqual(response.headers["Location"], expected_url)

        # Add the same item again
        payload2 = {
            "item_id": 101,
            "description": "Test Item",
            "price": 9.99,
            "quantity": 3,
        }
        response2 = self.client.post(f"/shopcarts/{user_id}", json=payload2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        data = response2.get_json()
        expected_url = f"http://localhost/shopcarts/{user_id}"
        self.assertIn("Location", response.headers)
        self.assertEqual(response.headers["Location"], expected_url)

        # The quantity should now be 2 + 3 = 5
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["quantity"], 5)
        self.assertAlmostEqual(data[0]["price"], payload["price"], places=2)

    def test_add_item_invalid_input(self):
        """It should return a 400 error if fields have invalid data types."""
        user_id = 1
        # Non-integer 'item_id'
        payload = {"item_id": "abc", "description": "Test Item", "price": 9.99}
        response = self.client.post(f"/shopcarts/{user_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)

    def test_add_item_missing_json(self):
        """It should return 400 when the request body is missing"""
        resp = self.client.post("/shopcarts/1", json=[])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing JSON payload", resp.get_json()["error"])

    def test_add_item_internal_server_error_update(self):
        with patch(
            "service.models.Shopcart.update", side_effect=Exception("Database error")
        ):
            user_id = 1
            # First, add the item
            payload = {
                "item_id": 101,
                "description": "Test Item",
                "price": 9.99,
                "quantity": 2,
            }
            response = self.client.post(f"/shopcarts/{user_id}", json=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Add the same item again
            payload2 = {
                "item_id": 101,
                "description": "Test Item",
                "price": 9.99,
                "quantity": 3,
            }
            response2 = self.client.post(f"/shopcarts/{user_id}", json=payload2)
            self.assertEqual(
                response2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            data = response2.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    def test_add_item_internal_server_error_create(self):
        with patch(
            "service.models.Shopcart.create", side_effect=Exception("Database error")
        ):
            user_id = 1
            # First, add the item
            payload = {
                "item_id": 101,
                "description": "Test Item",
                "price": 9.99,
                "quantity": 2,
            }
            response = self.client.post(f"/shopcarts/{user_id}", json=payload)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

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

    def test_list_shopcarts_server_error(self):
        """It should handle server errors gracefully"""
        # Create some test data to make sure the database is working initially
        self._populate_shopcarts(1)
        # Mock the database query to raise an exception
        with patch(
            "service.models.Shopcart.all", side_effect=Exception("Database error")
        ):
            resp = self.client.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")
            expected_error = "Internal server error: Database error"
            self.assertEqual(data["error"], expected_error)

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
        user_ids = set([cart["user_id"] for cart in data])
        self.assertEqual(user_ids, {1, 2})

        # Grab shopcart for user_id = 1
        resp = self.client.get("/shopcarts/1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data = resp.get_json()
        self.assertIsInstance(user_data, list)
        self.assertEqual(set([cart["user_id"] for cart in user_data]), {1})
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
        user_ids = set([cart["user_id"] for cart in data])
        self.assertEqual(user_ids, {1})

        # Grab shopcart for user_id = 2
        resp = self.client.get("/shopcarts/2")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_user_shopcart_server_error(self):
        """Read by user_id should handle server errors gracefully"""
        self._populate_shopcarts(count=1, user_id=1)
        with patch(
            "service.models.Shopcart.find_by_user_id",
            side_effect=Exception("Database error"),
        ):
            resp = self.client.get("/shopcarts/1")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")
            expected_error = "Internal server error: Database error"
            self.assertEqual(data["error"], expected_error)

    def test_update_shopcart_success(self):
        """It should update the quantity of multiple items in an existing shop cart"""
        user_id = 1
        # Using helper method to pre populate the cart
        shopcarts = self._populate_shopcarts(count=2, user_id=user_id)

        # Update quantities
        update_cart = {
            "items": [
                {"item_id": shopcarts[0].item_id, "quantity": 4},
                {"item_id": shopcarts[1].item_id, "quantity": 0},
            ]
        }

        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()

        # Updated cart should now have 1 item, since one was removed by setting quantity to 0
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["item_id"], shopcarts[0].item_id)
        self.assertEqual(data[0]["quantity"], 4)

    def test_update_shopcart_not_found(self):
        """It should return a 404 error when trying to update a non-existing shopcart."""
        user_id = 10
        update_cart = {"items": [{"item_id": 100, "quantity": 3}]}
        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)

    def test_update_shopcart_negative_quantity(self):
        """It should return a 400 error if a negative quantity is entered."""
        user_id = 1
        # Pre-populate cart with 1 item
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        # Update item with negative quantity
        update_cart = {"items": [{"item_id": shopcarts[0].item_id, "quantity": -2}]}
        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)

    def test_update_shopcart_missing_payload(self):
        """It should return a 400 error when no JSON payload is provided."""
        user_id = 1
        # Create a cart first
        self._populate_shopcarts(count=1, user_id=user_id)

        # Don't include any payload
        response = self.client.put(f"/shopcarts/{user_id}", json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Missing JSON payload")

    def test_update_shopcart_invalid_items_format(self):
        """It should return a 400 error when 'items' is not a list."""
        user_id = 1
        # Create a cart first
        self._populate_shopcarts(count=1, user_id=user_id)

        # 'items' is not a list but a dictionary
        update_cart = {"items": {"item_id": 1, "quantity": 3}}
        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid payload: 'items' must be a list")

    def test_update_shopcart_invalid_item_id_type(self):
        """It should return a 400 error when item_id is not an integer."""
        user_id = 1
        # Create a cart first
        self._populate_shopcarts(count=1, user_id=user_id)

        # item_id is a string
        update_cart = {"items": [{"item_id": "abc", "quantity": 3}]}
        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertTrue("Invalid input" in data["error"])

    def test_update_shopcart_missing_required_fields(self):
        """It should return a 400 error when required fields are missing."""
        user_id = 1
        # Create a cart first
        self._populate_shopcarts(count=1, user_id=user_id)

        # Missing 'quantity' field
        update_cart = {"items": [{"item_id": 1}]}
        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertTrue("Invalid input" in data["error"])

    def test_update_shopcart_delete_exception(self):
        """It should handle exceptions during item deletion."""
        user_id = 1
        # Create a cart first
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)

        # Update with quantity 0 to trigger deletion
        update_cart = {"items": [{"item_id": shopcarts[0].item_id, "quantity": 0}]}

        # Mock the delete method to raise an exception
        with patch(
            "service.models.Shopcart.delete", side_effect=Exception("Delete error")
        ):
            response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Delete error")

    def test_update_shopcart_update_exception(self):
        """It should handle exceptions during item update."""
        user_id = 1
        # Create a cart first
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)

        # Update with a new quantity
        update_cart = {"items": [{"item_id": shopcarts[0].item_id, "quantity": 10}]}

        # Mock the update method to raise an exception
        with patch(
            "service.models.Shopcart.update", side_effect=Exception("Update error")
        ):
            response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Update error")

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
        self.assertEqual(set([cart["user_id"] for cart in data]), {1})
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
            self.assertNotIn("created_at", response_item)
            self.assertNotIn("last_updated", response_item)

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
