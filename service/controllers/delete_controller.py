"""
DELETE Controller logic for Shopcart Service
"""

from flask import jsonify
from flask import current_app as app
from service.models import Shopcart
from service.common import status


def delete_shopcart_controller(user_id):
    """Delete an entire shopcart for a user"""
    app.logger.info("Request to delete shopcart for user_id: %s", user_id)

    try:
        # Find all items for this user
        user_items = Shopcart.find_by_user_id(user_id)

        if not user_items:
            app.logger.warning("No items found in shopcart for user_id: %s", user_id)
            return (
                jsonify({"error": f"Shopcart not found for user {user_id}"}),
                status.HTTP_404_NOT_FOUND,
            )
        # Delete each item in the shopcart
        for item in user_items:
            app.logger.info(
                "Deleting item %s from user %s's cart", item.item_id, user_id
            )
            item.delete()

        app.logger.info("Shopcart for user %s deleted", user_id)
        return {}, status.HTTP_204_NO_CONTENT

    except Exception as e:  # pylint: disable=broad-except
        app.logger.error(
            "Error deleting shopcart for user_id: %s - %s", user_id, str(e)
        )
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
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
