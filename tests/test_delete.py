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
import json
from unittest.mock import patch
from service.common import status
from service.common.error_handlers import DatabaseConnectionError
from .test_routes import TestShopcartService


######################################################################
#  T E S T   C A S E S
######################################################################


class TestShopcartDelete(TestShopcartService):
    """Test cases for delete operations"""

    ######################################################################
    #  Delete Shopcart Testcase
    ######################################################################

    def test_delete_shopcart(self):
        """It should delete an entire shopcart for a user"""
        user_id = 1
        # Create test data
        self._populate_shopcarts(count=3, user_id=user_id)

        # Send delete request
        response = self.client.delete(f"/shopcarts/{user_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

        # Verify the shopcart is deleted by trying to get it
        get_response = self.client.get(f"/shopcarts/{user_id}")
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_shopcart(self):
        """It should return 204 even when deleting a non-existent shopcart"""
        # Try to delete a shopcart for a user that doesn't exist
        non_existent_user_id = 9999
        response = self.client.delete(f"/shopcarts/{non_existent_user_id}")

        # Should still return 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_delete_shopcart_server_error(self):
        """It should handle server errors gracefully when deleting a shopcart"""
        user_id = 1
        # Create some test data
        self._populate_shopcarts(count=1, user_id=user_id)

        # Mock the database query to raise an exception
        with patch(
            "service.models.Shopcart.find_by_user_id",
            side_effect=Exception("Database error"),
        ):
            response = self.client.delete(f"/shopcarts/{user_id}")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            # Verify the response contains an error message
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    ######################################################################
    #  Delete Cart Item Testcase
    ######################################################################

    def test_delete_cart_item_success(self):
        """It should delete a specific item from a user's shopcart"""
        user_id = 1
        # Create test data with multiple items for the user
        shopcarts = self._populate_shopcarts(count=3, user_id=user_id)
        item_id = shopcarts[0].item_id

        # Verify item exists before deletion
        initial_response = self.client.get(f"/shopcarts/{user_id}/items/{item_id}")
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)

        # Delete the item
        delete_response = self.client.delete(f"/shopcarts/{user_id}/items/{item_id}")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(delete_response.data), 0)

        # Verify the item was deleted
        get_response = self.client.get(f"/shopcarts/{user_id}/items/{item_id}")
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify the cart still exists with remaining items
        cart_response = self.client.get(f"/shopcarts/{user_id}")
        self.assertEqual(cart_response.status_code, status.HTTP_200_OK)
        cart_data = cart_response.get_json()
        # Should have 2 items left
        self.assertEqual(len(cart_data[0]["items"]), 2)

    def test_delete_nonexistent_cart_item(self):
        """It should return 404 when trying to delete a non-existent item"""
        user_id = 1
        # Create a cart with some items
        self._populate_shopcarts(count=1, user_id=user_id)

        # Try to delete an item that doesn't exist
        non_existent_item_id = 9999
        response = self.client.delete(
            f"/shopcarts/{user_id}/items/{non_existent_item_id}"
        )

        # Should return 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn(
            f"Item with id {non_existent_item_id} was not found", data["error"]
        )

    def test_delete_cart_item_nonexistent_user(self):
        """It should return 404 when trying to delete an item for a non-existent user's cart"""
        # Try to delete an item for a user that doesn't exist
        non_existent_user_id = 9999
        response = self.client.delete(f"/shopcarts/{non_existent_user_id}/items/1")

        # Should return 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("was not found", data["error"])

    def test_delete_cart_item_server_error(self):
        """It should handle server errors gracefully when deleting an item"""
        user_id = 1
        # Create test data
        shopcarts = self._populate_shopcarts(count=1, user_id=user_id)
        item_id = shopcarts[0].item_id

        # Mock the delete method to raise an exception
        with patch(
            "service.models.Shopcart.delete", side_effect=Exception("Database error")
        ):
            response = self.client.delete(f"/shopcarts/{user_id}/items/{item_id}")

            # Verify the status code is 500 (Internal Server Error)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            # Verify the response contains an error message
            data = response.get_json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal server error: Database error")

    def test_delete_shopcart_item_with_error(self):
        """It should handle database errors when deleting items"""
        user_id = 900
        # Create the shopcart with a normal call
        shopcart = self._populate_shopcarts(count=1, user_id=user_id)
        # Get the item_id from the created shopcart
        item_id = shopcart[0].item_id

        # Mock the find method to simulate a database error
        with patch('service.models.Shopcart.find', side_effect=Exception("Database error")):
            response = self.client.delete(f"/shopcarts/{user_id}/items/{item_id}")
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.get_json()
            self.assertIn("error", data)
            self.assertIn("Database error", data["error"])

    ######################################################################
    #  Database Connection Error Testcase
    ######################################################################

    def test_database_connection_error(self):
        """It should handle database connection errors"""
        with patch("service.models.Shopcart.all", side_effect=DatabaseConnectionError("DB connection error")):
            resp = self.app.get("/shopcarts")
            self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            data = json.loads(resp.data)
            self.assertIn("status", data)
            self.assertEqual(data["status"], status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Service Unavailable")
