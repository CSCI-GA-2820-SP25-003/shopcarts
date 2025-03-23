"""
GET Controller logic for Shopcart Service
"""

from werkzeug.exceptions import HTTPException
from flask import request, jsonify, abort
from flask import current_app as app
from service.models import Shopcart
from service.common import status, helpers


def get_shopcarts_controller():
    """List all shopcarts grouped by user"""

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
            return jsonify({"error": str(ve)}), status.HTTP_400_BAD_REQUEST

    # Group items by user_id
    user_items = {}
    for item in all_items:
        if item.user_id not in user_items:
            user_items[item.user_id] = []
        user_items[item.user_id].append(item.serialize())

    # Create the response list
    for user_id, items in user_items.items():
        shopcarts_list.append({"user_id": user_id, "items": items})

    return jsonify(shopcarts_list), status.HTTP_200_OK


def get_user_shopcart_controller(user_id):
    """Gets the shopcart for a specific user id"""
    app.logger.info("Request to get shopcart for user_id: '%s'", user_id)

    try:
        try:
            user_items = helpers.get_filtered_user_items(user_id)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), status.HTTP_400_BAD_REQUEST

        if not user_items:
            return abort(
                status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
            )

        try:
            range_filters = helpers.extract_filters()
        except ValueError as ve:
            return jsonify({"error": str(ve)}), status.HTTP_400_BAD_REQUEST

        filtered_items = helpers.apply_range_filters(user_items, range_filters)

        user_list = [{"user_id": user_id, "items": []}]
        for item in filtered_items:
            user_list[0]["items"].append(item.serialize())
        return jsonify(user_list), status.HTTP_200_OK
    except HTTPException as e:
        raise e
    except Exception as e:  # pylint: disable=broad-except
        app.logger.error(f"Error reading shopcart for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_user_shopcart_items_controller(user_id):
    """Gets all items in a specific user's shopcart"""
    app.logger.info("Request to get all items for user_id: '%s'", user_id)

    try:
        user_items = Shopcart.find_by_user_id(user_id=user_id)

        if not user_items:
            return abort(
                status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
            )

        # Just return the serialized items directly as a list
        items_list = [{"user_id": user_id, "items": []}]
        for item in user_items:
            data = item.serialize()
            del data["created_at"]
            del data["last_updated"]
            items_list[0]["items"].append(data)
        return jsonify(items_list), status.HTTP_200_OK
    except HTTPException as e:
        raise e
    except Exception as e:  # pylint: disable=broad-except
        app.logger.error(f"Error reading items for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_cart_item_controller(user_id, item_id):
    """Gets a specific item from a user's shopcart"""
    app.logger.info("Request to get item %s for user_id: %s", item_id, user_id)

    try:
        # First check if the user exists by trying to get any items for this user
        user_items = Shopcart.find_by_user_id(user_id=user_id)
        if not user_items:
            return abort(
                status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
            )

        # Now try to find the specific item
        cart_item = Shopcart.find(user_id, item_id)
        if not cart_item:
            return (
                jsonify(
                    {"error": f"Item {item_id} not found in user {user_id}'s cart"}
                ),
                status.HTTP_404_NOT_FOUND,
            )

        # Return the serialized item
        return jsonify(cart_item.serialize()), status.HTTP_200_OK

    except HTTPException as e:
        raise e
    except Exception as e:  # pylint: disable=broad-except
        app.logger.error(f"Error retrieving item {item_id} for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
