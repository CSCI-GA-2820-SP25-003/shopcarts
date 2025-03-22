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

from flask import jsonify
from flask import current_app as app  # Import Flask application
from service.common import status  # HTTP Status Codes

from service.controllers.get_controller import (
    get_shopcarts_controller,
    get_user_shopcart_controller,
    get_user_shopcart_items_controller,
    get_cart_item_controller,
)

from service.controllers.post_controller import (
    add_product_to_cart_controller,
    add_to_or_create_cart_controller,
    checkout_controller,
)

from service.controllers.put_controller import (
    update_cart_item_controller,
    update_shopcart_controller,
)

from service.controllers.delete_controller import (
    delete_shopcart_controller,
    delete_shopcart_item_controller,
)


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


############################################################
# H E A L T H   E N D P O I N T
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return {"status": "OK"}, status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# GET ROUTES


@app.route("/shopcarts", methods=["GET"])
def list_shopcarts():
    """List all shopcarts grouped by user"""
    return get_shopcarts_controller()


@app.route("/shopcarts/<int:user_id>", methods=["GET"])
def get_user_shopcart(user_id):
    """
    Gets the shopcart for a specific user id
    This endpoint retrieves all items in a user's shopping cart
    with optional price filtering using query parameters:
    - min-price: Show only items with price >= min-price
    - max-price: Show only items with price <= max-price
    Examples:
        GET /shopcarts/123?max-price=50
        GET /shopcarts/123?min-price=10
        GET /shopcarts/123?min-price=10&max-price=50
    """
    return get_user_shopcart_controller(user_id)


@app.route("/shopcarts/<int:user_id>/items", methods=["GET"])
def get_user_shopcart_items(user_id):
    """Gets all items in a specific user's shopcart"""
    return get_user_shopcart_items_controller(user_id)


@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["GET"])
def get_cart_item(user_id, item_id):
    """Gets a specific item from a user's shopcart"""
    return get_cart_item_controller(user_id, item_id)


# POST ROUTES


@app.route("/shopcarts/<int:user_id>", methods=["POST"])
def add_to_or_create_cart(user_id):
    """Add an item to a user's cart or update quantity if it already exists."""
    return add_to_or_create_cart_controller(user_id)


@app.route("/shopcarts/<int:user_id>/items", methods=["POST"])
def add_product_to_cart(user_id):
    """
    Add a product to a user's shopping cart or update quantity if it already exists.
    Product data (name, price, stock, purchase_limit, etc.) is taken from the request body,
    """
    return add_product_to_cart_controller(user_id)


# PUT ROUTES


@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["PUT"])
def update_cart_item(user_id, item_id):
    """Update a specific item in a user's shopping cart."""
    return update_cart_item_controller(user_id, item_id)


@app.route("/shopcarts/<int:user_id>", methods=["PUT"])
def update_shopcart(user_id):
    """Update an existing shopcart."""
    return update_shopcart_controller(user_id)


# DELETE ROUTES


@app.route("/shopcarts/<int:user_id>", methods=["DELETE"])
def delete_shopcart(user_id):
    """Delete an entire shopcart for a user"""
    return delete_shopcart_controller(user_id)


@app.route("/shopcarts/<int:user_id>/items/<int:item_id>", methods=["DELETE"])
def delete_shopcart_item(user_id, item_id):
    """
    Delete a specific item from a user's shopping cart
    This endpoint removes a single item from a shopping cart while preserving the cart
    and any other items that may be in it
    """
    return delete_shopcart_item_controller(user_id, item_id)


# ACTION ROUTE


@app.route("/shopcarts/<int:user_id>/checkout", methods=["POST"])
def checkout(user_id):
    """Finalize a user's cart and proceed with payment."""
    return checkout_controller(user_id)
