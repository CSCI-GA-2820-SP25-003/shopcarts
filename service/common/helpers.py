"""
Helper functions for services
"""

from datetime import datetime
from flask import request, jsonify
from service.common import status
from service.models import Shopcart
from sqlalchemy import and_, or_
from datetime import timedelta, datetime

RANGE_OPERATORS = {
    "lt": lambda field, value: field < value,
    "lte": lambda field, value: field <= value,
    "gt": lambda field, value: field > value,
    "gte": lambda field, value: field >= value,
}


def parse_datetime(value):
    """Convert 'YYYY-MM-DD' to a datetime object."""
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.") from exc


def apply_filter(field, cast_type, value):
    """Applies a filter condition based on the field type and value format."""
    try:
        if "~" in value:
            _, operator, filter_value = value.split("~")
            filter_value = (
                parse_datetime(filter_value)
                if cast_type is datetime
                else cast_type(filter_value)
            )

            if cast_type is datetime and operator in ["lt", "lte"]:
                filter_value += timedelta(days=1) - timedelta(seconds=1)

            if operator not in RANGE_OPERATORS:
                raise ValueError(f"Invalid operator: {operator}")

            return RANGE_OPERATORS[operator](field, filter_value)

        if cast_type is datetime and "," in value:
            date_conditions = [
                and_(
                    field >= parse_datetime(date_str.strip()),
                    field
                    <= parse_datetime(date_str.strip())
                    + timedelta(days=1)
                    - timedelta(seconds=1),
                )
                for date_str in value.split(",")
            ]
            return or_(*date_conditions)

        if cast_type is datetime:
            start_date = parse_datetime(value)
            return and_(
                field >= start_date,
                field <= start_date + timedelta(days=1) - timedelta(seconds=1),
            )

        if "," in value:
            return field.in_([cast_type(v.strip()) for v in value.split(",")])
        return field == cast_type(value)

    except ValueError as exc:
        # Preserve the original error message
        if "Invalid date format" in str(exc):
            raise exc  # This will keep the message expected by the test
        raise ValueError(f"Invalid filter value: {value}") from exc


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


VALID_FIELDS = {
    "user_id": (Shopcart.user_id, int),
    "price": (Shopcart.price, float),
    "created_at": (Shopcart.created_at, datetime),
}


def fetch_all_shopcarts():
    """Retrieve all shopcarts from the database."""
    return Shopcart.all()


def fetch_filtered_shopcarts():
    """Retrieve shopcarts based on request filters and query parameters."""
    try:
        # ✅ Step 1: Extract standard filters (from helpers)
        filters = extract_filters()
        filtered_items = Shopcart.find_by_ranges(
            filters=filters
        )  # ✅ Preserves range filtering

        # ✅ Step 2: Apply additional filtering based on query parameters
        query_params = request.args.to_dict(flat=False)
        additional_filters = build_filter_conditions(query_params)

        if additional_filters:
            filtered_items = Shopcart.query.filter(and_(*additional_filters)).all()

        return filtered_items

    except ValueError as exc:
        raise ValueError(f"Invalid filter parameter: {exc}") from exc


def build_filter_conditions(query_params):
    """Builds SQLAlchemy filter conditions from query parameters."""
    filters = []
    for key, values in query_params.items():
        if key in VALID_FIELDS:
            field, cast_type = VALID_FIELDS[key]
            conditions = [apply_filter(field, cast_type, value) for value in values]
            if conditions:
                filters.append(or_(*conditions))
    return filters


def format_shopcarts_response(items):
    """Formats the shopcart response grouped by user."""
    user_items = {}
    for item in items:
        user_items.setdefault(item.user_id, []).append(item.serialize())

    return [
        {"user_id": user_id, "items": items} for user_id, items in user_items.items()
    ]
