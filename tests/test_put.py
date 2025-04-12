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
from unittest.mock import patch
from service.common import status
from .test_routes import TestShopcartService


######################################################################
#  T E S T   C A S E S
######################################################################


class TestShopcartPut(TestShopcartService):
    """Test cases for put operations"""

    ######################################################################
    #  Put Shopcart Testcase
    ######################################################################

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
        self.assertEqual("Quantity must be greater than 0.", data["error"])

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

    def test_update_shopcart_item_not_found(self):
        """It should return a 404 error when updating a shopcart with an item that doesn't exist"""
        user_id = 1
        # Create a shopcart with one item
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        existing_item_id = shopcarts[0].item_id

        # Try to update with a mix of existing and non-existing items
        non_existent_item_id = 9999  # An item ID that doesn't exist
        update_cart = {
            "items": [
                {"item_id": existing_item_id, "quantity": 10},
                {"item_id": non_existent_item_id, "quantity": 5},
            ]
        }

        response = self.client.put(f"/shopcarts/{user_id}", json=update_cart)

        # Check response status and error message
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn(f"Item {non_existent_item_id} not found", data["error"])

    def test_update_cart_item_success(self):
        """It should update a specific item in a user's shopcart"""
        user_id = 1
        # Pre-populate the cart with one item using the helper method
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        item_id = shopcarts[0].item_id

        update_item = {"quantity": 4}
        response = self.client.put(
            f"/shopcarts/{user_id}/items/{item_id}", json=update_item
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["quantity"], 4)
        self.assertEqual(data["item_id"], item_id)
        self.assertEqual(data["user_id"], user_id)

    def test_update_cart_item_remove(self):
        """It should remove the item if the quantity is set to 0"""
        user_id = 1
        # Pre-populate the cart with one item.
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        item_id = shopcarts[0].item_id

        update_item = {"quantity": 0}
        response = self.client.put(
            f"/shopcarts/{user_id}/items/{item_id}", json=update_item
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # Confirm that item was removed
        self.assertIn("message", data)
        self.assertEqual(data["message"], f"Item {item_id} removed from cart")

    def test_update_cart_item_not_found(self):
        """It should return a 404 error if the item does not exist in the user's shopcart"""
        user_id = 1
        # Ensure there is at least one item in the cart so the cart exists.
        self._populate_shopcarts(count=1, user_id=user_id)
        item_id = 203
        update_item = {"quantity": 3}
        response = self.client.put(
            f"/shopcarts/{user_id}/items/{item_id}", json=update_item
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)

    def test_update_cart_item_invalid_input(self):
        """It should return a 400 error if the quantity is negative."""
        user_id = 1
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        item_id = shopcarts[0].item_id
        update_item = {"quantity": -1}
        response = self.client.put(
            f"/shopcarts/{user_id}/items/{item_id}", json=update_item
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertEqual("Quantity must be greater than 0.", data["error"])

    def test_update_cart_item_missing_payload(self):
        """It should return a 400 error if no JSON is provided."""
        user_id = 1
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        item_id = shopcarts[0].item_id
        response = self.client.put(f"/shopcarts/{user_id}/items/{item_id}", json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("error", data)
