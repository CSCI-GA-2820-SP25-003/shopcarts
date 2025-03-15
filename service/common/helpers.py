"""
Helper functions for services
"""

from flask import jsonify
from service.common import status
from service.models import Shopcart


def validate_request_data(data):
    """Extract and validate request data."""
    try:
        product_id = int(data["product_id"])
        quantity = int(data.get("quantity", 1))
        name = str(data.get("name", ""))
        price = float(data.get("price", 0.0))

        stock = data.get("stock")
        purchase_limit = data.get("purchase_limit")

        if stock is not None:
            stock = int(stock)
        if purchase_limit is not None:
            purchase_limit = int(purchase_limit)

        return product_id, quantity, name, price, stock, purchase_limit
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Invalid input: {e}") from e


def validate_stock_and_limits(quantity, stock, purchase_limit):
    """Check stock availability and purchase limits."""
    if stock is not None and stock < 1:
        return (
            jsonify({"error": "Product is out of stock"}),
            status.HTTP_400_BAD_REQUEST,
        )

    if stock is not None and quantity > stock:
        return (
            jsonify({"error": f"Only {stock} units are available"}),
            status.HTTP_400_BAD_REQUEST,
        )

    if purchase_limit is not None and quantity > purchase_limit:
        return (
            jsonify({"error": f"Cannot exceed purchase limit of {purchase_limit}"}),
            status.HTTP_400_BAD_REQUEST,
        )

    return None


def update_or_create_cart_item(user_id, product_data):
    """Update an existing cart item or create a new one."""
    product_id = product_data["product_id"]
    quantity = product_data["quantity"]
    name = product_data["name"]
    price = product_data["price"]
    stock = product_data["stock"]
    purchase_limit = product_data["purchase_limit"]
    cart_item = Shopcart.find(user_id, product_id)

    if cart_item:
        new_quantity = cart_item.quantity + quantity

        # Validate against stock and purchase limits
        error_response = validate_stock_and_limits(new_quantity, stock, purchase_limit)
        if error_response:
            raise ValueError(error_response[0].json["error"])  # Extract error message

        cart_item.quantity = new_quantity
        cart_item.update()
    else:
        new_item = Shopcart(
            user_id=user_id,
            item_id=product_id,
            description=name,
            quantity=quantity,
            price=price,
        )
        new_item.create()

    return Shopcart.find_by_user_id(user_id)


def validate_items_list(data):
    """Validate the 'items' field in the request payload."""
    items = data.get("items")
    if not items or not isinstance(items, list):
        raise ValueError("Invalid payload: 'items' must be a list")
    return items


def process_cart_updates(user_id, items):
    """Update or remove items in the user's shopping cart."""
    for item in items:
        try:
            item_id = int(item["item_id"])
            quantity = int(item["quantity"])
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid input: {e}") from e

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        # Attempt to update/remove the cart item
        update_cart_item_helper(user_id, item_id, quantity)


def update_cart_item_helper(user_id, item_id, quantity):
    """Update or remove a cart item based on the given quantity."""
    cart_item = Shopcart.find(user_id, item_id)
    if not cart_item:
        # Raise an exception if the item does not exist
        raise LookupError(f"Item {item_id} not found in user {user_id}'s cart")

    if quantity == 0:
        cart_item.delete()
    else:
        cart_item.quantity = quantity
        cart_item.update()
