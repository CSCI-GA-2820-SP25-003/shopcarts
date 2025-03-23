"""
Helper functions for services
"""

from datetime import datetime
from flask import request, jsonify
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


def parse_range_param(param_name, cast_func, date_format=None):
    value = request.args.get(param_name)
    if not value:
        return None, None

    parts = value.split(",")
    if len(parts) != 2:
        raise ValueError(f"{param_name} must have two comma-separated values")

    try:
        if date_format:
            min_val = datetime.strptime(parts[0], date_format)
            max_val = datetime.strptime(parts[1], date_format)
        else:
            min_val = cast_func(parts[0])
            max_val = cast_func(parts[1])
    except Exception:
        raise ValueError(f"{param_name} values are invalid or malformed")

    if min_val > max_val:
        raise ValueError(f"min value cannot be greater than max value in {param_name}")

    return min_val, max_val


def extract_filters():
    """Extract range filters from request arguments."""
    filters = {}
    ranges = [
        ("range_price", "min_price", "max_price", float, None),
        ("range_qty", "min_qty", "max_qty", int, None),
        ("range_created_at", "min_date", "max_date", None, "%d-%m-%Y"),
        ("range_last_updated", "min_update", "max_update", None, "%d-%m-%Y"),
    ]

    for param, min_key, max_key, cast_type, date_format in ranges:
        if date_format:
            min_val, max_val = parse_range_param(
                param, cast_type, date_format=date_format
            )
        else:
            min_val, max_val = parse_range_param(param, cast_type)

        if min_val is not None:
            filters[min_key] = min_val
            filters[max_key] = max_val

    return filters


def parse_operator_value(value_string):
    """Parse a value string with optional operator prefixes.

    Format: ~operator~value where operator can be lt, lte, gt, or gte
    If no operator is present, equality is assumed.

    Returns:
        tuple: (operator, value) where operator is one of eq, lt, lte, gt, gte
    """
    if not value_string.startswith("~"):
        return "eq", value_string

    parts = value_string.split("~")
    if len(parts) < 3:
        raise ValueError(f"Invalid operator format: {value_string}")

    operator = parts[1].lower()
    value = "~".join(parts[2:])

    if operator not in ["lt", "lte", "gt", "gte"]:
        raise ValueError(f"Unsupported operator: {operator}")

    return operator, value


def extract_item_filters(request_args):
    """Extract filter parameters from request arguments.

    Args:
        request_args: The request arguments from Flask's request.args

    Returns:
        dict: Filter parameters with their operators and values
    """
    filter_fields = [
        "quantity",
        "price",
        "created_at",
        "last_updated",
        "description",
        "item_id",
    ]
    filters = {}

    for field in filter_fields:
        if field in request_args:
            try:
                operator, value = parse_operator_value(request_args[field])
                filters[field] = {"operator": operator, "value": value}
            except ValueError as e:
                raise ValueError(f"Error parsing filter for {field}: {str(e)}")

    return filters


def apply_range_filters(items, range_filters):
    """
    Applies range-based filters (for quantity and price) to a list of items.
    Returns a filtered list of items.
    """
    if not range_filters:
        return items

    filtered_items = []
    for item in items:
        # Check quantity range if present
        if "min_qty" in range_filters and "max_qty" in range_filters:
            if not (
                range_filters["min_qty"] <= item.quantity <= range_filters["max_qty"]
            ):
                continue

        # Check price range if present
        if "min_price" in range_filters and "max_price" in range_filters:
            price_val = float(item.price)
            if not (
                range_filters["min_price"] <= price_val <= range_filters["max_price"]
            ):
                continue

        filtered_items.append(item)
    return filtered_items
