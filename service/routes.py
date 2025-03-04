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
YourResourceModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete YourResourceModel
"""

from flask import jsonify, request
from flask import current_app as app  # Import Flask application
from service.models import Shopcart
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...


@app.route("/shopcart/<int:user_id>", methods=["POST"])
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
            return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST
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
            return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    # Return the updated cart for the user
    cart = [item.serialize() for item in Shopcart.find_by_user_id(user_id)]
    return jsonify(cart), status.HTTP_200_OK


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
        for i in user_items:
            print(i.serialize())

        if not user_items:
            return jsonify([]), status.HTTP_404_NOT_FOUND

        user_list = [{"user_id": user_id, "items": []}]
        for item in user_items:
            user_list[0]["items"].append(item.serialize())
        return jsonify(user_list), status.HTTP_200_OK

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
            return jsonify([]), status.HTTP_404_NOT_FOUND

        # Just return the serialized items directly as a list
        items_list = [item.serialize() for item in user_items]
        return jsonify(items_list), status.HTTP_200_OK

    except Exception as e:
        app.logger.error(f"Error reading items for user_id: '{user_id}'")
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.route("/shopcarts/<int:user_id>/items", methods=["POST"])
def add_product_to_cart(user_id):
    """
    Add a product to a user's shopping cart or update quantity if it already exists.
    Product data (name, price, stock, purchase_limit, etc.) is taken from the request body.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), status.HTTP_400_BAD_REQUEST

    try:
        product_info = extract_product_info(data)
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), status.HTTP_400_BAD_REQUEST

    error_response = validate_product_constraints(product_info)
    if error_response:
        return error_response

    return process_cart_update(user_id, product_info)


def extract_product_info(data):
    """Extracts and validates product-related data from request."""
    try:
        return {
            "product_id": int(data["product_id"]),
            "quantity": int(data.get("quantity", 1)),
            "name": str(data.get("name", "")),
            "price": float(data.get("price", 0.0)),
            "stock": int(data["stock"]) if "stock" in data else None,
            "purchase_limit": (
                int(data["purchase_limit"]) if "purchase_limit" in data else None
            ),
        }
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(e)


def validate_product_constraints(product_info):
    """Validates stock and purchase limit constraints before adding to cart."""
    stock, purchase_limit, quantity = (
        product_info["stock"],
        product_info["purchase_limit"],
        product_info["quantity"],
    )

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

    return None  # No validation errors


def process_cart_update(user_id, product_info):
    """Handles adding/updating product in the shopping cart."""
    product_id, quantity = product_info["product_id"], product_info["quantity"]
    stock, purchase_limit = product_info["stock"], product_info["purchase_limit"]

    cart_item = Shopcart.find(user_id, product_id)

    if cart_item:
        return update_existing_cart_item(cart_item, quantity, stock, purchase_limit)
    else:
        return create_new_cart_item(user_id, product_info)


def update_existing_cart_item(cart_item, quantity, stock, purchase_limit):
    """Updates an existing cart item while checking stock and purchase limits."""
    new_quantity = cart_item.quantity + quantity

    if stock is not None and new_quantity > stock:
        return (
            jsonify({"error": f"Cannot exceed {stock} units in stock"}),
            status.HTTP_400_BAD_REQUEST,
        )
    if purchase_limit is not None and new_quantity > purchase_limit:
        return (
            jsonify({"error": f"Cannot exceed purchase limit of {purchase_limit}"}),
            status.HTTP_400_BAD_REQUEST,
        )

    cart_item.quantity = new_quantity
    try:
        cart_item.update()
    except Exception as e:
        app.logger.error("Error updating cart item: %s", e)
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    return get_cart_response(cart_item.user_id)


def create_new_cart_item(user_id, product_info):
    """Creates a new cart item."""
    new_item = Shopcart(
        user_id=user_id,
        item_id=product_info["product_id"],
        description=product_info["name"],
        quantity=product_info["quantity"],
        price=product_info["price"],
    )
    try:
        new_item.create()
    except Exception as e:
        app.logger.error("Error creating cart item: %s", e)
        return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

    return get_cart_response(user_id)


def get_cart_response(user_id):
    """Fetches updated cart and returns serialized data."""
    cart_items = Shopcart.find_by_user_id(user_id)
    return jsonify([item.serialize() for item in cart_items]), status.HTTP_200_OK
