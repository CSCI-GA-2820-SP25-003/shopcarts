"""
PUT Controller logic for Shopcart Service
"""

from flask import request
from flask import current_app as app
from service.common import status
from service.models import Shopcart
from service.common.helpers import (
    validate_items_list,
    process_cart_updates,
)


def update_shopcart_controller(user_id):
    """Update an existing shopcart."""
    # Initialize response variables
    status_code = status.HTTP_200_OK
    response_body = {}
    response_headers = {}

    # Get and validate JSON payload
    data = request.get_json()
    if not data:
        response_body = {"error": "Missing JSON payload"}
        status_code = status.HTTP_400_BAD_REQUEST
    elif not Shopcart.find_by_user_id(user_id):
        response_body = {"error": f"Shopcart for user {user_id} not found"}
        status_code = status.HTTP_404_NOT_FOUND
    else:
        # Process the request if basic validation passes
        try:
            items = validate_items_list(data)
            process_cart_updates(user_id, items)
            # Get the updated cart for response
            updated_cart = [
                item.serialize() for item in Shopcart.find_by_user_id(user_id)
            ]
            response_body = updated_cart
        except ValueError as e:
            app.logger.error("Cart update validation error: %s", e)
            response_body = {"error": str(e)}
            status_code = status.HTTP_400_BAD_REQUEST
        except LookupError as e:
            # Item-not-found error from update_cart_item_helper
            response_body = {"error": str(e)}
            status_code = status.HTTP_404_NOT_FOUND
        except Exception as e:  # pylint: disable=broad-except
            app.logger.error("Cart update error: %s", e)
            response_body = {"error": str(e)}
            status_code = status.HTTP_400_BAD_REQUEST

    # Return the appropriate response
    return response_body, status_code, response_headers


def update_cart_item_controller(user_id, item_id):
    """Update a specific item in a user's shopping cart."""
    data = request.get_json()
    if not data:
        return {"error": "Missing JSON payload"}, status.HTTP_400_BAD_REQUEST

    quantity = int(data.get("quantity"))

    cart_item = Shopcart.find(user_id, item_id)
    if not cart_item:
        return (
            {"error": f"Item {item_id} not found cart"},
            status.HTTP_404_NOT_FOUND,
        )

    if quantity == 0:
        cart_item.delete()
        return (
            {"message": f"Item {item_id} removed from cart"},
            status.HTTP_200_OK,
        )

    cart_item.quantity = quantity
    try:
        cart_item.update()
    except ValueError as e:
        response_body = {"error": str(e)}
        return response_body, status.HTTP_400_BAD_REQUEST
    return cart_item.serialize(), status.HTTP_200_OK
