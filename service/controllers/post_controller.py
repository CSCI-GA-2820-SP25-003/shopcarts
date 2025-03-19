"""
POST Controller logic for Shopcart Service
"""

from json import JSONDecodeError
from flask import request, jsonify, url_for
from flask import current_app as app
from service.common import status
from service.common.helpers import (
    validate_request_data,
    validate_stock_and_limits,
    update_or_create_cart_item,
)
from service.models import Shopcart


def add_to_or_create_cart_controller(user_id):
    """Add a product to a user's shopping cart or update quantity if it already exists."""
    # Step 1: Parse request data
    data, error_response = parse_request_data()
    if error_response:
        return error_response

    item_id, description, price, quantity = (
        data["item_id"],
        data["description"],
        data["price"],
        data["quantity"],
    )

    # Step 2: Check if item exists in cart
    cart_item = Shopcart.find(user_id, item_id)
    if cart_item:
        # Update existing item
        update_response = update_existing_cart_item(cart_item, quantity)
        if update_response:
            return update_response
    else:
        # Create a new cart entry
        create_response = create_new_cart_item(
            user_id, item_id, description, price, quantity
        )
        if create_response:
            return create_response

    # Step 3: Return updated cart
    return fetch_updated_cart(user_id)


def parse_request_data():
    """Parse and validate the incoming JSON request."""
    try:
        data = request.get_json()
        if not data:
            return None, (
                jsonify({"error": "Missing JSON payload"}),
                status.HTTP_400_BAD_REQUEST,
            )

        return {
            "item_id": int(data["item_id"]),
            "description": str(data["description"]),
            "price": float(data["price"]),
            "quantity": int(data.get("quantity", 1)),
        }, None
    except (KeyError, ValueError, TypeError, JSONDecodeError) as e:
        return None, (
            jsonify({"error": f"Invalid input: {e}"}),
            status.HTTP_400_BAD_REQUEST,
        )


def update_existing_cart_item(cart_item, quantity):
    """Update quantity of an existing cart item."""
    cart_item.quantity += quantity
    try:
        cart_item.update()
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return None


def create_new_cart_item(user_id, item_id, description, price, quantity):
    """Create a new shopping cart entry."""
    new_item = Shopcart(
        user_id=user_id,
        item_id=item_id,
        description=description,
        quantity=quantity,
        price=price,
    )
    try:
        new_item.create()
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return None


def fetch_updated_cart(user_id):
    """Fetch and return the updated shopping cart for the user."""
    location_url = url_for("get_user_shopcart", user_id=user_id, _external=True)
    cart = [item.serialize() for item in Shopcart.find_by_user_id(user_id)]
    return jsonify(cart), status.HTTP_201_CREATED, {"Location": location_url}


def add_product_to_cart_controller(user_id):
    """Add a product to a user's shopping cart or update quantity if it already exists."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), status.HTTP_400_BAD_REQUEST

    try:
        product_id, quantity, name, price, stock, purchase_limit = (
            validate_request_data(data)
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    error_response = validate_stock_and_limits(quantity, stock, purchase_limit)
    if error_response:
        return error_response

    # Look for an existing cart item (composite key: user_id & product_id)
    try:
        product_data = {
            "product_id": product_id,
            "quantity": quantity,
            "name": name,
            "price": price,
            "stock": stock,
            "purchase_limit": purchase_limit,
        }
        cart_items = update_or_create_cart_item(user_id, product_data)
    except Exception as e:  # pylint: disable=broad-except
        app.logger.error("Cart update error: %s", e)
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    location_url = url_for("get_user_shopcart", user_id=user_id, _external=True)
    return (
        jsonify([item.serialize() for item in cart_items]),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )
