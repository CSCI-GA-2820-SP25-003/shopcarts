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
from flask import current_app as app
from flask_restx import Api, Resource, fields, reqparse
from service.common import status

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
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Shopcarts REST API Service",
    description="This is the Shopcarts REST API Service.",
    default="shopcarts",
    default_label="Shopcarts operations",
    doc="/apidocs",
    prefix="/api",
)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
# GET INFO
######################################################################
@app.route("/info")
def info():
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


# Define the models for Swagger documentation

shopcart_item_without_timestamps_model = api.model(
    "ShopcartItemWithoutTimestamps",
    {
        "user_id": fields.Integer(required=True, description="The user ID"),
        "item_id": fields.Integer(required=True, description="The item ID"),
        "description": fields.String(required=True, description="The item description"),
        "quantity": fields.Integer(required=True, description="The item quantity"),
        "price": fields.Float(required=True, description="The item price"),
    },
)

shopcart_items_without_timestamps_model = api.model(
    "ShopcartItemsWithoutTimestamps",
    {
        "user_id": fields.Integer(required=True, description="The user ID"),
        "items": fields.List(
            fields.Nested(shopcart_item_without_timestamps_model),
            required=True,
            description="List of items in the cart",
        ),
    },
)

shopcart_item_model = api.model(
    "ShopCartItem",
    {
        "user_id": fields.Integer(required=True, description="The user ID"),
        "item_id": fields.Integer(required=True, description="The item ID"),
        "description": fields.String(
            required=True, description="Description of the item"
        ),
        "quantity": fields.Integer(required=True, description="Quantity of the item"),
        "price": fields.Float(required=True, description="Price of the item"),
        "created_at": fields.DateTime(readOnly=True, description="Creation timestamp"),
        "last_updated": fields.DateTime(
            readOnly=True, description="Last update timestamp"
        ),
    },
)

shopcart_model = api.model(
    "ShopCart",
    {
        "user_id": fields.Integer(required=True, description="The user ID"),
        "items": fields.List(
            fields.Nested(shopcart_item_model), description="Items in the shopcart"
        ),
    },
)

# Define query string arguments for filtering
shopcart_args = reqparse.RequestParser()
shopcart_args.add_argument(
    "user_id", type=str, location="args", help="Filter by user ID"
)
shopcart_args.add_argument(
    "item_id", type=str, location="args", help="Filter by item ID"
)
shopcart_args.add_argument(
    "description", type=str, location="args", help="Filter by description"
)
shopcart_args.add_argument(
    "quantity",
    type=str,
    location="args",
    help="Filter by quantity or use operators like ~gt~, ~lt~",
)
shopcart_args.add_argument(
    "price",
    type=str,
    location="args",
    help="Filter by price or use operators like ~gt~, ~lt~",
)
shopcart_args.add_argument(
    "created_at", type=str, location="args", help="Filter by creation date"
)
shopcart_args.add_argument(
    "last_updated", type=str, location="args", help="Filter by last update date"
)
shopcart_args.add_argument(
    "price_range",
    type=str,
    location="args",
    help="Filter by price range (format: min,max)",
)
shopcart_args.add_argument(
    "quantity_range",
    type=str,
    location="args",
    help="Filter by quantity range (format: min,max)",
)
shopcart_args.add_argument(
    "min-price", type=float, location="args", help="Filter by minimum price"
)
shopcart_args.add_argument(
    "max-price", type=float, location="args", help="Filter by maximum price"
)
shopcart_args.add_argument(
    "min-qty", type=int, location="args", help="Filter by minimum quantity"
)
shopcart_args.add_argument(
    "max-qty", type=int, location="args", help="Filter by maximum quantity"
)

######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@api.route("/shopcarts", strict_slashes=False)
class ShopcartsCollection(Resource):
    """Handles all interactions with collections of Shopcarts"""

    @api.doc("list_shopcarts")
    @api.expect(shopcart_args, validate=False)
    def get(self):
        """Lists all shopcarts grouped by user"""
        app.logger.info("Request to list all shopcarts")
        return get_shopcarts_controller()


@api.route("/shopcarts/<int:user_id>", strict_slashes=False)
class ShopcartsResource(Resource):
    """Handles all interactions with a single Shopcart resource"""

    @api.doc("get_shopcart")
    @api.expect(shopcart_args, validate=False)
    @api.response(200, "Success")
    @api.response(404, "Shopcart not found")
    @api.response(500, "Internal Server Error")
    def get(self, user_id):
        """Gets the shopcart for a specific user id"""
        app.logger.info("Request to get shopcart for user_id: '%s'", user_id)
        return get_user_shopcart_controller(user_id)

    @api.doc("add_to_cart")
    @api.expect(
        api.model(
            "AddToCart",
            {
                "item_id": fields.Integer(required=True, description="The item ID"),
                "description": fields.String(
                    required=True, description="Description of the item"
                ),
                "price": fields.Float(required=True, description="Price of the item"),
                "quantity": fields.Integer(
                    default=1, description="Quantity of the item"
                ),
            },
        )
    )
    @api.response(201, "Item created successfully")
    @api.response(400, "Invalid input")
    @api.response(500, "Internal Server Error")
    def post(self, user_id):
        """Add an item to a user's cart or update quantity if it already exists."""
        app.logger.info("Request to add item to cart for user_id: '%s'", user_id)
        cart, status_code = add_to_or_create_cart_controller(user_id)
        if status_code == status.HTTP_201_CREATED:
            location_url = api.url_for(
                ShopcartsResource, user_id=user_id, _external=True
            )
            return cart, status_code, {"Location": location_url}
        return cart, status_code

    @api.doc("update_shopcart")
    @api.expect(
        api.model(
            "UpdateShopcart",
            {
                "items": fields.List(
                    fields.Nested(
                        api.model(
                            "ShopCartItemUpdate",
                            {
                                "item_id": fields.Integer(
                                    required=True,
                                    description="ID of the item to update",
                                ),
                                "quantity": fields.Integer(
                                    required=True,
                                    description="New quantity for the item",
                                ),
                            },
                        )
                    ),
                    required=True,
                    description="List of items to update in the cart",
                )
            },
        )
    )
    @api.response(200, "Shopcart updated successfully")
    @api.response(400, "Invalid input")
    @api.response(404, "Shopcart or item not found")
    def put(self, user_id):
        """Update an existing shopcart"""
        app.logger.info("Request to update shopcart for user_id: '%s'", user_id)
        return update_shopcart_controller(user_id)

    @api.doc("delete_shopcart")
    def delete(self, user_id):
        """Delete an entire shopcart for a user"""
        app.logger.info("Request to delete shopcart for user_id: '%s'", user_id)
        return delete_shopcart_controller(user_id)


@api.route("/shopcarts/<int:user_id>/items", strict_slashes=False)
class ShopcartItemsCollection(Resource):
    """Handles all interactions with the items in a specific user's shopcart"""

    @api.doc("get_shopcart_items")
    @api.response(200, "Success")
    @api.response(404, "User not found")
    @api.response(500, "Internal Server Error")
    def get(self, user_id):
        """Gets all items in a specific user's shopcart"""
        app.logger.info("Request to get all items for user_id: '%s'", user_id)
        return get_user_shopcart_items_controller(user_id)

    @api.doc("add_product_to_cart")
    @api.expect(
        api.model(
            "AddProductToCart",
            {
                "product_id": fields.Integer(
                    required=True, description="The product ID"
                ),
                "name": fields.String(required=True, description="Name of the product"),
                "price": fields.Float(
                    required=True, description="Price of the product"
                ),
                "quantity": fields.Integer(
                    default=1, description="Quantity of the product"
                ),
                "stock": fields.Integer(required=True, description="Available stock"),
                "purchase_limit": fields.Integer(
                    required=False, description="Purchase limit per customer"
                ),
            },
        )
    )
    @api.response(201, "Item successfully added")
    @api.response(400, "Invalid input")
    @api.response(500, "Internal Server Error")
    def post(self, user_id):
        """Add a product to a user's shopping cart or update quantity if it already exists."""
        app.logger.info("Request to add product to cart for user_id: '%s'", user_id)
        cart, status_code = add_product_to_cart_controller(user_id)

        if status_code == status.HTTP_201_CREATED:
            # Generate the Location header
            location_url = api.url_for(
                ShopcartsResource, user_id=user_id, _external=True
            )
            return cart, status_code, {"Location": location_url}

        return cart, status_code


@api.route("/shopcarts/<int:user_id>/items/<int:item_id>", strict_slashes=False)
class ShopcartItemsResource(Resource):
    """Handles all interactions with a specific item in a shopcart"""

    @api.doc("get_cart_item")
    @api.response(200, "Success")
    @api.response(404, "User or item not found")
    @api.response(500, "Internal Server Error")
    def get(self, user_id, item_id):
        """Gets a specific item from a user's shopcart"""
        app.logger.info("Request to get item %s for user_id: %s", item_id, user_id)
        return get_cart_item_controller(user_id, item_id)

    @api.doc("update_cart_item")
    @api.expect(
        api.model(
            "UpdateCartItem",
            {
                "quantity": fields.Integer(
                    required=True, description="Updated quantity of the item"
                )
            },
        )
    )
    @api.response(200, "Item updated")
    @api.response(400, "Invalid input")
    @api.response(404, "Item not found")
    def put(self, user_id, item_id):
        """Update a specific item in a user's shopping cart"""
        app.logger.info("Request to update item %s for user_id: %s", item_id, user_id)
        return update_cart_item_controller(user_id, item_id)

    @api.doc("delete_shopcart_item")
    @api.response(204, "Item deleted")
    @api.response(404, "Item not found")
    @api.response(500, "Internal Server Error")
    def delete(self, user_id, item_id):
        """Delete a specific item from a user's shopping cart"""
        app.logger.info(
            "Request to delete item %s from user_id: %s shopping cart", item_id, user_id
        )
        return delete_shopcart_item_controller(user_id, item_id)


@api.route("/shopcarts/<int:user_id>/checkout", strict_slashes=False)
class CheckoutResource(Resource):
    """Handles checkout operations for a shopcart"""

    @api.doc("checkout_shopcart")
    @api.response(200, "Checkout successful")
    @api.response(400, "Bad Request")
    @api.response(404, "Shopcart not found")
    @api.response(500, "Internal Server Error")
    def post(self, user_id):
        """Finalize a user's cart and proceed with payment"""
        app.logger.info("Request to checkout shopcart for user_id: '%s'", user_id)
        return checkout_controller(user_id)
