"""API namespace definitions and route bindings for the Shopcart service.

Includes endpoint declarations for GET, POST, PUT, and DELETE operations on user carts,
with Swagger documentation and query parameter filters.
"""

from flask import jsonify
from flask_restx import Resource
from werkzeug.exceptions import BadRequest
from service.common import status as http_status

from service.controllers import (
    get_controller,
    put_controller,
    post_controller,
    delete_controller,
)

from service.controllers.namespace_models import (
    shopcart_ns,
    user_cart_model,
    shopcart_item_model,
    shopcart_product_model,
    shopcart_item_list_model,
    quantity_only_model,
    shopcart_item_post_model,
)


# === ENDPOINTS ===


@shopcart_ns.route("/")
@shopcart_ns.doc(
    params={
        "item_id": "Filter by item ID (exact match)",
        "description": "Filter by description (substring match)",
        "min_price": "Minimum price",
        "max_price": "Maximum price",
        "min_quantity": "Minimum quantity",
        "max_quantity": "Maximum quantity",
        "created_after": "Filter by created_at after (ISO format)",
        "created_before": "Filter by created_at before (ISO format)",
        "updated_after": "Filter by last_updated after (ISO format)",
        "updated_before": "Filter by last_updated before (ISO format)",
    }
)
class ShopcartList(Resource):
    """Handles listing all user shopcarts, with optional filters."""

    @shopcart_ns.doc("list_shopcarts", summary="List all shopcarts grouped by user")
    @shopcart_ns.marshal_list_with(user_cart_model, code=200, description="Success")
    @shopcart_ns.response(400, "Invalid query parameters")
    def get(self):
        """List all shopcarts. You can apply query filters."""
        resp, status_code = get_controller.get_shopcarts_controller()
        return resp.get_json(force=True), status_code


@shopcart_ns.route("/<int:user_id>")
@shopcart_ns.param("user_id", "The user identifier")
@shopcart_ns.doc(
    params={
        "item_id": "Filter by item ID (exact match)",
        "description": "Filter by description (substring match)",
        "min_price": "Minimum price",
        "max_price": "Maximum price",
        "min_quantity": "Minimum quantity",
        "max_quantity": "Maximum quantity",
        "created_after": "Filter by created_at after (ISO format)",
        "created_before": "Filter by created_at before (ISO format)",
        "updated_after": "Filter by last_updated after (ISO format)",
        "updated_before": "Filter by last_updated before (ISO format)",
    }
)
class ShopcartByUser(Resource):
    """Handles retrieval of a single user's cart with optional filters."""

    @shopcart_ns.doc("get_user_shopcart", summary="Get shopcart for a specific user")
    @shopcart_ns.marshal_with(user_cart_model, code=200, description="Success")
    @shopcart_ns.response(400, "Bad request or invalid filters")
    @shopcart_ns.response(404, "User not found")
    def get(self, user_id):
        """Returns the entire shopcart for a given user_id, with optional filters."""
        resp, status_code = get_controller.get_user_shopcart_controller(user_id)
        return resp.get_json(force=True), status_code


@shopcart_ns.route("/<int:user_id>/items")
@shopcart_ns.param("user_id", "The user identifier")
class ShopcartUserItems(Resource):
    """Lists all items for a user without timestamps."""

    @shopcart_ns.doc(
        "get_user_shopcart_items", summary="Get all items in a user's cart"
    )
    @shopcart_ns.marshal_list_with(shopcart_item_model, code=200, description="Success")
    @shopcart_ns.response(404, "User not found")
    def get(self, user_id):
        """Returns all items from the user's cart without timestamps."""
        resp, status_code = get_controller.get_user_shopcart_items_controller(user_id)
        return resp.get_json(force=True), status_code


@shopcart_ns.route("/<int:user_id>/items/<int:item_id>")
@shopcart_ns.param("user_id", "The user ID")
@shopcart_ns.param("item_id", "The item ID")
class ShopcartItem(Resource):
    """Fetches a specific cart item by user and item ID."""

    @shopcart_ns.doc("get_cart_item", summary="Get a specific item from a user's cart")
    @shopcart_ns.marshal_with(shopcart_item_model, code=200, description="Success")
    @shopcart_ns.response(404, "User or item not found")
    def get(self, user_id, item_id):
        """Fetch a specific item from the user's cart."""
        resp, status_code = get_controller.get_cart_item_controller(user_id, item_id)
        return resp.get_json(force=True), status_code


@shopcart_ns.route("/<int:user_id>/add")
@shopcart_ns.param("user_id", "The user ID")
class ShopcartAdd(Resource):
    """Adds or updates items in a user's cart via direct input."""

    @shopcart_ns.doc(
        "add_to_or_create_cart", summary="Add item or update quantity in a user's cart"
    )
    @shopcart_ns.expect(shopcart_item_post_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=201, description="Item added or updated"
    )
    @shopcart_ns.response(400, "Invalid input")
    def post(self, user_id):
        """Adds or updates an item in the user's cart."""
        response = post_controller.add_to_or_create_cart_controller(user_id)
        if isinstance(response, tuple):
            data, status_code, *rest = response
            headers = rest[0] if rest else {}
            return data.get_json(force=True), status_code, headers
        return response.get_json(force=True), response.status_code, {}


@shopcart_ns.route("/<int:user_id>/products")
@shopcart_ns.param("user_id", "The user ID")
class AddProduct(Resource):
    """Adds product with validation like stock and purchase limits."""

    @shopcart_ns.doc("add_product", summary="Add a product with validations")
    @shopcart_ns.expect(shopcart_product_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=201, description="Product added"
    )
    @shopcart_ns.response(400, "Bad request or validation error")
    def post(self, user_id):
        """Adds a validated product to the user's cart."""
        response = post_controller.add_product_to_cart_controller(user_id)
        if isinstance(response, tuple):
            data, status_code, headers = response
            return data.get_json(force=True), status_code, headers
        return response.get_json(force=True), response.status_code


@shopcart_ns.route("/<int:user_id>/checkout")
@shopcart_ns.param("user_id", "The user ID")
class Checkout(Resource):
    """Triggers the checkout process for the user's cart."""

    @shopcart_ns.doc(
        "checkout_cart", summary="Finalize the cart and proceed to payment"
    )
    @shopcart_ns.response(200, "Checkout successful")
    @shopcart_ns.response(400, "Validation error")
    @shopcart_ns.response(500, "Internal server error")
    def post(self, user_id):
        """Process checkout for a user's cart."""
        try:
            response = post_controller.checkout_controller(user_id)
            if isinstance(response, tuple):
                data, status_code = response
                return data.get_json(force=True), status_code
            return response.get_json(force=True), response.status_code
        except (BadRequest, ValueError) as e:
            return jsonify({"error": str(e)}), http_status.HTTP_400_BAD_REQUEST


@shopcart_ns.route("/<int:user_id>")
@shopcart_ns.param("user_id", "The user ID")
class ShopcartModify(Resource):
    """Updates or deletes the entire user's cart."""

    @shopcart_ns.doc("update_shopcart", summary="Update the user's entire cart")
    @shopcart_ns.expect(shopcart_item_list_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=200, description="Cart updated"
    )
    @shopcart_ns.response(400, "Bad request")
    @shopcart_ns.response(404, "Shopcart not found")
    def put(self, user_id):
        """Replaces all items in the user's cart with the provided list."""
        return put_controller.update_shopcart_controller(user_id)

    @shopcart_ns.doc("delete_shopcart", summary="Delete the entire user's cart")
    @shopcart_ns.response(204, "Cart deleted")
    @shopcart_ns.response(500, "Internal server error")
    def delete(self, user_id):
        """Deletes all items from the user's cart."""
        return delete_controller.delete_shopcart_controller(user_id)


@shopcart_ns.route("/<int:user_id>/items/<int:item_id>")
@shopcart_ns.param("user_id", "The user ID")
@shopcart_ns.param("item_id", "The item ID")
class CartItemModify(Resource):
    """Updates or deletes a specific item in the cart."""

    @shopcart_ns.doc("update_cart_item", summary="Update a single item in the cart")
    @shopcart_ns.expect(quantity_only_model, validate=True)
    @shopcart_ns.marshal_with(
        shopcart_item_model, code=200, description="Item updated or removed"
    )
    @shopcart_ns.response(400, "Invalid input or negative quantity")
    @shopcart_ns.response(404, "Item or cart not found")
    def put(self, user_id, item_id):
        """Updates the quantity of a specific item in the cart."""
        return put_controller.update_cart_item_controller(user_id, item_id)

    @shopcart_ns.doc("delete_cart_item", summary="Delete a specific item from the cart")
    @shopcart_ns.response(204, "Item deleted")
    @shopcart_ns.response(404, "Item not found in cart")
    @shopcart_ns.response(500, "Internal server error")
    def delete(self, user_id, item_id):
        """Deletes a specific item from the user's cart."""
        return delete_controller.delete_shopcart_item_controller(user_id, item_id)
