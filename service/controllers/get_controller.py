"""
GET Controller logic for Shopcart Service
"""

from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import HTTPException
from flask import jsonify, abort, request
from flask import current_app as app
from service.models import Shopcart
from service.common import status
from service.common.helpers import (
    fetch_filtered_shopcarts,
    fetch_all_shopcarts,
    format_shopcarts_response,
)


VALID_FIELDS = {
    "user_id": (Shopcart.user_id, int),
    "item_id": (Shopcart.item_id, int),
    "description": (Shopcart.description, str),
    "quantity": (Shopcart.quantity, int),
    "price": (Shopcart.price, float),
    "created_at": (Shopcart.created_at, datetime),
    "last_updated": (Shopcart.last_updated, datetime),
}


def get_shopcarts_controller():
    """List all shopcarts grouped by user with optional filters."""
    app.logger.info("Request to list shopcarts with filters")

    try:
        items = fetch_filtered_shopcarts() if request.args else fetch_all_shopcarts()
        response_data = format_shopcarts_response(items)

        return jsonify(response_data), status.HTTP_200_OK

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
