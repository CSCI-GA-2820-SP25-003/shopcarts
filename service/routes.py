######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Shopcarts Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Shopcarts
"""

from flask import jsonify, request, abort, url_for
from flask import current_app as app  # Import Flask application
from service.models import Shopcart
from service.common import status  # HTTP Status Codes
from werkzeug.exceptions import HTTPException


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response with API metadata"""
    app.logger.info("Request for Root URL")

    return (
        jsonify(
            name="Shopcart REST API Service",
            version="1.0",
            paths={
                "/shopcarts": {
                    "GET": "Lists all shopcarts grouped by user",
                },
                "/shopcarts/{user_id}": {
                    "POST": "Adds an item to a user's shopcart or updates quantity if it already exists",
                    "GET": "Retrieves the shopcart with metadata",
                    "PUT": "Updates the entire shopcart",
                    "DELETE": "Deletes the entire shopcart (all items)",
                },
                "/shopcarts/{user_id}/items": {
                    "POST": "Adds a product to a user's shopcart or updates quantity",
                    "GET": "Lists all items in the user's shopcart (without metadata)",
                },
                "/shopcarts/{user_id}/items/{item_id}": {
                    "GET": "Retrieves a specific item from the user's shopcart",
                    "PUT": "Updates a specific item in the shopcart",
                    "DELETE": "Removes an item from the shopcart",
                },
            },
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...


@app.route("/shopcarts/<int:user_id>", methods=["POST"])
def add_to_or_create_cart(user_id):
    """Add an item to a user's cart or update quantity if it already exists."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), status.HTTP_400_BAD_REQUEST

    try:
        item_id = int(data["item_id"])
        description = str(data["description"])
        price = float(data["price"])
        quantity = int(data.get("quantity", 1))
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), status.HTTP_400_BAD_REQUEST

    # Check if this item is already in the user's cart
    cart_item = Shopcart.find(user_id, item_id)
    if cart_item:
        # Update the existing item's quantity
        cart_item.quantity += quantity
        try:
            cart_item.update()
        except Exception as e:
            return (
                jsonify({"error": f"Internal server error: {str(e)}"}),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        # Create a new cart entry
        new_item = Shopcart(
            user_id=user_id,
            item_id=item_id,
            description=description,
            quantity=quantity,
            price=price,
        )
        try:
            new_item.create()
        except Exception as e:
            return (
                jsonify({"error": f"Internal server error: {str(e)}"}),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # Return the updated cart for the user
    location_url = url_for("get_user_shopcart", user_id=user_id, _external=True)
    cart = [item.serialize() for item in Shopcart.find_by_user_id(user_id)]
    return jsonify(cart), status.HTTP_201_CREATED, {"Location": location_url}


@app.route("/shopcarts", methods=["GET"])
def list_shopcarts():
    """List all shopcarts grouped by user"""
    app.logger.info("Request to list shopcarts")

    try:
        # Initialize an empty list to store unique user shopcarts
        shopcarts_list = []

        # Get all shopcarts grouped by user_id
        all_items = Shopcart.all()

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

    except Exception as e:
        app.logger.error(f"Error listing shopcarts: {str(e)}")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.route("/shopcarts/<int:user_id>", methods=["GET"])
def get_user_shopcart(user_id):
    """Gets the shopcart for a specific user id"""
    app.logger.info("Request to get shopcart for user_id: '%s'", user_id)

    try:

        user_items = Shopcart.find_by_user_id(user_id=user_id)

        if not user_items:
            return abort(
                status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
            )

        user_list = [{"user_id": user_id, "items": []}]
        for item in user_items:
            user_list[0]["items"].append(item.serialize())
        return jsonify(user_list), status.HTTP_200_OK
    except HTTPException as e:
        raise e
    except Exception as e:
        app.logger.error(f"Error reading shopcart for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.route("/shopcarts/<int:user_id>/items", methods=["GET"])
def get_user_shopcart_items(user_id):
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
    except Exception as e:
        app.logger.error(f"Error reading items for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["DELETE"])
def delete_shopcart_item(user_id, item_id):
    """
    Delete a specific item from a user's shopping cart
    This endpoint removes a single item from a shopping cart while preserving the cart
    and any other items that may be in it
    """
    app.logger.info("Request to delete item_id: %s from user_id: %s shopping cart", item_id, user_id)

    try:
        # Find the specific item in the user's cart
        cart_item = Shopcart.find(user_id, item_id)

        # Check if the item exists in the cart
        if not cart_item:
            return (
                jsonify({"error": f"Item with id {item_id} was not found in user {user_id}'s cart"}),
                status.HTTP_404_NOT_FOUND
            )

        # Delete the item from the cart
        cart_item.delete()

        # Verify the deletion was successful
        if Shopcart.find(user_id, item_id):
            return (
                jsonify({"error": f"Failed to delete item {item_id} from user {user_id}'s cart"}),
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return the updated cart contents (which might be empty but still exists)
        user_items = Shopcart.find_by_user_id(user_id)
        items_list = [item.serialize() for item in user_items]

        return jsonify(items_list), status.HTTP_200_OK

    except Exception as e:
        app.logger.error(f"Error deleting item {item_id} from user {user_id}'s cart: {str(e)}")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )