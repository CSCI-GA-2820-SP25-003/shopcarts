"""
GET Controller logic for Shopcart Service
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import HTTPException
from flask import jsonify, abort, request
from flask import current_app as app
from service.models import Shopcart
from service.common import status, helpers


RANGE_OPERATORS = {
    "lt": lambda field, value: field < value,
    "lte": lambda field, value: field <= value,
    "gt": lambda field, value: field > value,
    "gte": lambda field, value: field >= value,
}

VALID_FIELDS = {
    "user_id": (Shopcart.user_id, int),
    "item_id": (Shopcart.item_id, int),
    "description": (Shopcart.description, str),
    "quantity": (Shopcart.quantity, int),
    "price": (Shopcart.price, float),
    "created_at": (Shopcart.created_at, datetime),
    "last_updated": (Shopcart.last_updated, datetime),
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


def get_shopcarts_controller():
    """List all shopcarts grouped by user"""
    """List all shopcarts with optional filtering based on query parameters"""
    app.logger.info("Request to list shopcarts with filters")

    # Initialize an empty list to store unique user shopcarts
    shopcarts_list = []

    if not request.args:
        app.logger.info("Request to list shopcarts")
        # Get all shopcarts grouped by user_id
        all_items = Shopcart.all()

    else:
        app.logger.info("Request to list shopcarts with query range")
        filters = {}
        try:
            filters = helpers.extract_filters()
            all_items = Shopcart.find_by_ranges(filters=filters)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        all_items = Shopcart.find_by_ranges(filters=filters)

    # Group items by user_id
    user_items = {}
    for item in all_items:
        if item.user_id not in user_items:
            user_items[item.user_id] = []
        user_items[item.user_id].append(item.serialize())
    try:
        query_params = request.args.to_dict(flat=False)
        filters = []

        for key, values in query_params.items():
            if key in VALID_FIELDS:
                field, cast_type = VALID_FIELDS[key]
                conditions = [apply_filter(field, cast_type, value) for value in values]

                if conditions:
                    filters.append(or_(*conditions))

        filtered_items = (
            Shopcart.query.filter(and_(*filters)).all() if filters else Shopcart.all()
        )

        user_items = {}
        for item in filtered_items:
            user_items.setdefault(item.user_id, []).append(item.serialize())

    # Create the response list
    for user_id, items in user_items.items():
        shopcarts_list.append({"user_id": user_id, "items": items})
        shopcarts_list = [
            {"user_id": user_id, "items": items}
            for user_id, items in user_items.items()
        ]

    return jsonify(shopcarts_list), status.HTTP_200_OK

    except ValueError as exc:
        app.logger.error(f"Invalid filter parameter: {exc}")
        return jsonify({"error": str(exc)}), status.HTTP_400_BAD_REQUEST

    except SQLAlchemyError as exc:
        app.logger.error(f"Database error: {exc}", exc_info=True)
        raise InternalServerError("A database error occurred.") from exc


def get_user_shopcart_controller(user_id):
    """Gets the shopcart for a specific user id"""
    app.logger.info("Request to get shopcart for user_id: '%s'", user_id)

    try:
        user_items = Shopcart.find_by_user_id(user_id=user_id)

        if not user_items:
            abort(status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found.")

        return (
            jsonify(
                [
                    {
                        "user_id": user_id,
                        "items": [item.serialize() for item in user_items],
                    }
                ]
            ),
            status.HTTP_200_OK,
        )

    except HTTPException as exc:
        raise exc

    except SQLAlchemyError as exc:
        app.logger.error(
            f"Database error while reading shopcart for user_id '{user_id}': {exc}",
            exc_info=True,
        )
        raise InternalServerError("A database error occurred.") from exc


def get_user_shopcart_items_controller(user_id):
    """Gets all items in a specific user's shopcart"""
    app.logger.info("Request to get all items for user_id: '%s'", user_id)

    try:
        user_items = Shopcart.find_by_user_id(user_id=user_id)

        if not user_items:
            abort(status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found.")

        items_list = [
            {
                "user_id": user_id,
                "items": [
                    {
                        k: v
                        for k, v in item.serialize().items()
                        if k not in ["created_at", "last_updated"]
                    }
                    for item in user_items
                ],
            }
        ]

        return jsonify(items_list), status.HTTP_200_OK

    except HTTPException as exc:
        raise exc

    except SQLAlchemyError as exc:
        app.logger.error(
            f"Database error while retrieving items for user_id '{user_id}': {exc}",
            exc_info=True,
        )
        raise InternalServerError("A database error occurred.") from exc


def get_cart_item_controller(user_id, item_id):
    """Gets a specific item from a user's shopcart"""
    app.logger.info("Request to get item %s for user_id: %s", item_id, user_id)

    try:
        user_items = Shopcart.find_by_user_id(user_id=user_id)
        if not user_items:
            abort(status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found.")

        cart_item = Shopcart.find(user_id, item_id)
        if not cart_item:
            return (
                jsonify(
                    {"error": f"Item {item_id} not found in user {user_id}'s cart"}
                ),
                status.HTTP_404_NOT_FOUND,
            )

        return jsonify(cart_item.serialize()), status.HTTP_200_OK

    except HTTPException as exc:
        raise exc

    except SQLAlchemyError as exc:
        app.logger.error(
            f"Database error while retrieving item {item_id} for user_id '{user_id}': {exc}",
            exc_info=True,
        )
        raise InternalServerError("A database error occurred.") from exc
