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
    """Extract filter parameters including direct attributes, ranges, and lists."""

    filter_fields = [
        "user_id",
        "quantity",
        "price",
        "created_at",
        "last_updated",
        "description",
        "item_id",
    ]
    filters = {}

    for field in filter_fields:
        apply_field_filter(field, request_args, filters)

    try:
        apply_price_bounds_filter(request_args, filters)
    except ValueError as e:
        raise ValueError(f"Error in price filters: {str(e)}")
    return filters


def apply_price_bounds_filter(request_args, filters):
    """Apply min-price / max-price filters, but raise if price already handled."""

    # If price is already handled AND min/max-price are also present, raise error
    if ("price" in filters or "price_range" in filters) and (
        "min-price" in request_args or "max-price" in request_args
    ):
        raise ValueError(
            "Cannot use both 'price' or 'price_range' and 'min-price'/'max-price' in the same request."
        )

    min_price = request_args.get("min-price")
    max_price = request_args.get("max-price")
    if min_price and max_price:
        filters["price"] = {
            "operator": "range",
            "value": [min_price, max_price],
        }
    elif max_price:
        filters["price"] = {"operator": "lte", "value": max_price}
    elif min_price:
        filters["price"] = {"operator": "gte", "value": min_price}


def apply_field_filter(field, request_args, filters):
    """Apply a filter for a single field to the filters dict."""
    range_key = f"{field}_range"

    if range_key in request_args:
        value_string = request_args[range_key]
        try:
            start, end = map(str.strip, value_string.split(","))
            filters[field] = {"operator": "range", "value": [start, end]}
        except ValueError:
            raise ValueError(
                f"Invalid range format for {range_key}: expected start,end"
            )

    elif field in request_args:
        value_string = request_args[field]

        if "," in value_string:
            values = [v.strip() for v in value_string.split(",")]
            filters[field] = {"operator": "in", "value": values}
        else:
            try:
                operator, value = parse_operator_value(value_string)
                filters[field] = {"operator": operator, "value": value}
            except ValueError as e:
                raise ValueError(f"Error parsing filter for {field}: {str(e)}")
