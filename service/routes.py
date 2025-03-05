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
        raise ValueError(f"Invalid input: {e}")


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


def update_or_create_cart_item(
    user_id, product_id, quantity, name, price, stock, purchase_limit
):
    """Update an existing cart item or create a new one."""
    cart_item = Shopcart.find(user_id, product_id)

    if cart_item:
        return update_existing_cart_item(cart_item, quantity, stock, purchase_limit)
    else:
        return create_new_cart_item(user_id, product_info)


def update_existing_cart_item(cart_item, quantity, stock, purchase_limit):
    """Updates an existing cart item while checking stock and purchase limits."""
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


@app.route("/shopcarts/<int:user_id>/items", methods=["POST"])
def add_product_to_cart(user_id):
    """
    Add a product to a user's shopping cart or update quantity if it already exists.
    Product data (name, price, stock, purchase_limit, etc.) is taken from the request body,
    """
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
        cart_items = update_or_create_cart_item(
            user_id, product_id, quantity, name, price, stock, purchase_limit
        )
    except Exception as e:
        app.logger.error("Cart update error: %s", e)
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    location_url = url_for("get_user_shopcart", user_id=user_id, _external=True)
    return (
        jsonify([item.serialize() for item in cart_items]),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["PUT"])
def update_cart_item(user_id, item_id):
    """Update a specific item in a user's shopping cart."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), status.HTTP_400_BAD_REQUEST

    quantity = int(data.get("quantity"))
    if quantity < 0:
        return (
            jsonify({"error": "Quantity cannot be negative"}),
            status.HTTP_400_BAD_REQUEST,
        )

    cart_item = Shopcart.find(user_id, item_id)
    if not cart_item:
        return (
            jsonify({"error": f"Item {item_id} not found in user {user_id}'s cart"}),
            status.HTTP_404_NOT_FOUND,
        )

    if quantity == 0:
        cart_item.delete()
        return (
            jsonify({"message": f"Item {item_id} removed from cart"}),
            status.HTTP_200_OK,
        )

    cart_item.quantity = quantity
    cart_item.update()
    return jsonify(cart_item.serialize()), status.HTTP_200_OK


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
            raise ValueError(f"Invalid input: {e}")

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        update_cart_item_helper(user_id, item_id, quantity)


def update_cart_item_helper(user_id, item_id, quantity):
    """Update or remove a cart item based on the given quantity."""
    cart_item = Shopcart.find(user_id, item_id)

    if cart_item:
        if quantity == 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.update()


@app.route("/shopcarts/<int:user_id>", methods=["PUT"])
def update_shopcart(user_id):
    """Update an existing shopcart."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), status.HTTP_400_BAD_REQUEST

    # Validate items list
    try:
        items = validate_items_list(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    # Ensure the shopcart exists
    if not Shopcart.find_by_user_id(user_id):
        return (
            jsonify({"error": f"Shopcart for user {user_id} not found"}),
            status.HTTP_404_NOT_FOUND,
        )

    # Process cart updates
    try:
        process_cart_updates(user_id, items)
    except Exception as e:
        app.logger.error("Cart update error: %s", e)
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    # Return updated cart
    updated_cart = [item.serialize() for item in Shopcart.find_by_user_id(user_id)]
    return jsonify(updated_cart), status.HTTP_200_OK


@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["GET"])
def get_cart_item(user_id, item_id):
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
    except Exception as e:
        app.logger.error(f"Error retrieving item {item_id} for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.route("/shopcarts/<int:user_id>", methods=["DELETE"])
def delete_shopcart(user_id):
    """Delete an entire shopcart for a user"""
    app.logger.info("Request to delete shopcart for user_id: %s", user_id)

    try:
        # Find all items for this user
        user_items = Shopcart.find_by_user_id(user_id)

        # Delete each item in the shopcart
        for item in user_items:
            app.logger.info(
                "Deleting item %s from user %s's cart", item.item_id, user_id
            )
            item.delete()

        app.logger.info("Shopcart for user %s deleted", user_id)
        return {}, status.HTTP_204_NO_CONTENT

    except Exception as e:
        app.logger.error(
            "Error deleting shopcart for user_id: %s - %s", user_id, str(e)
        )
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
    app.logger.info(
        "Request to delete item_id: %s from user_id: %s shopping cart", item_id, user_id
    )

    try:
        # Find the specific item in the user's cart
        cart_item = Shopcart.find(user_id, item_id)

        # Check if the item exists in the cart
        if not cart_item:
            return (
                jsonify(
                    {
                        "error": f"Item with id {item_id} was not found in user {user_id}'s cart"
                    }
                ),
                status.HTTP_404_NOT_FOUND,
            )

        # Delete the item from the cart
        cart_item.delete()

        # Return empty response with 204 NO CONTENT status
        app.logger.info(
            "Item with ID: %d deleted from user %d's cart", item_id, user_id
        )
        return {}, status.HTTP_204_NO_CONTENT

    except Exception as e:
        app.logger.error(
            f"Error deleting item {item_id} from user {user_id}'s cart: {str(e)}"
        )
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
