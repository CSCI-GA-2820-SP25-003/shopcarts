"""
DELETE Controller logic for Shopcart Service
"""

from unittest.mock import patch
from flask import jsonify
from flask import current_app as app
from service.models import Shopcart
from service.common import status


def delete_shopcart_controller(user_id):
    """Delete the entire shopcart for a user"""
    app.logger.info("Request to delete user shopcart with id: %s", user_id)
    try:
        # Try to find any items for this user
        shopcart_items = Shopcart.find_by_user_id(user_id)

        # Even if no items found, we'll still return 204 (common pattern for deletes)
        # as the end state is what the client wanted
        for item in shopcart_items:
            item.delete()

        return "", status.HTTP_204_NO_CONTENT

    except Exception as e:  # pylint: disable=broad-except
        # Intentionally broad to catch database errors
        app.logger.error("Error deleting shopcart for user_id: %s: %s", user_id, str(e))
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def delete_shopcart_item_controller(user_id, item_id):
    """Delete a specific item from a user's shopping cart"""
    app.logger.info(
        "Request to delete item_id: %s from user_id: %s shopping cart", item_id, user_id
    )

    try:
        # Find the specific item in the user's cart
        cart_item = Shopcart.find(user_id, item_id)

        # Check if the item exists in the cart
        if not cart_item:
            return (
                jsonify(
                    {
                        "error": f"Item with id {item_id} was not found in user {user_id}'s cart"
                    }
                ),
                status.HTTP_404_NOT_FOUND,
            )

        # Delete the item from the cart
        cart_item.delete()

        # Return empty response with 204 NO CONTENT status
        app.logger.info(
            "Item with ID: %d deleted from user %d's cart", item_id, user_id
        )
        return {}, status.HTTP_204_NO_CONTENT

    except Exception as e:  # pylint: disable=broad-except
        app.logger.error(
            f"Error deleting item {item_id} from user {user_id}'s cart: {str(e)}"
        )
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def test_read_user_shopcart_server_error(self):
    """Read by user_id should handle server errors gracefully"""
    self._populate_shopcarts(count=1, user_id=1)
    # Use a different patch point that will definitely be called in get_controller
    with patch(
        "service.models.Shopcart.find_by_user_id_with_filter",
        side_effect=Exception("Database error"),
    ):
        resp = self.client.get("/shopcarts/1")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Database error", data["error"])


def test_delete_shopcart_with_error_during_delete(self):
    """It should handle delete errors during shopcart deletion"""
    user_id = 800
    # Create test data
    items = self._populate_shopcarts(count=2, user_id=user_id)

    # Mock the delete method to raise an exception
    with patch.object(
        Shopcart,
        'delete',
        side_effect=Exception("Database delete error")
    ):
        # Send delete request
        response = self.client.delete(f"/shopcarts/{user_id}")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("Database delete error", data["error"])

        # Verify items still exist
        for item in items:
            found = Shopcart.find(user_id, item.item_id)
            self.assertIsNotNone(found)
