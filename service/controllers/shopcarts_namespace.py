# service/controllers/shopcart_namespace.py

from flask_restx import Namespace, Resource, fields
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
class ShopcartList(Resource):
    @shopcart_ns.doc("list_shopcarts", summary="List all shopcarts grouped by user")
    @shopcart_ns.marshal_list_with(user_cart_model, code=200, description="Success")
    @shopcart_ns.response(400, "Invalid query parameters")
    def get(self):
        """List all shopcarts. You can apply query filters."""
        resp, status = get_controller.get_shopcarts_controller()
        return resp.get_json(force=True), status


@shopcart_ns.route("/<int:user_id>")
@shopcart_ns.param("user_id", "The user identifier")
class ShopcartByUser(Resource):
    @shopcart_ns.doc("get_user_shopcart", summary="Get shopcart for a specific user")
    @shopcart_ns.marshal_with(user_cart_model, code=200, description="Success")
    @shopcart_ns.response(400, "Bad request or invalid filters")
    @shopcart_ns.response(404, "User not found")
    def get(self, user_id):
        """Returns the entire shopcart for a given user_id, with optional filters."""
        resp, status = get_controller.get_user_shopcart_controller(user_id)
        return resp.get_json(force=True), status


@shopcart_ns.route("/<int:user_id>/items")
@shopcart_ns.param("user_id", "The user identifier")
class ShopcartUserItems(Resource):
    @shopcart_ns.doc(
        "get_user_shopcart_items", summary="Get all items in a user's cart"
    )
    @shopcart_ns.marshal_list_with(shopcart_item_model, code=200, description="Success")
    @shopcart_ns.response(404, "User not found")
    def get(self, user_id):
        """Lists all items in a user's shopcart."""
        resp, status = get_controller.get_user_shopcart_items_controller(user_id)
        return resp.get_json(force=True), status


@shopcart_ns.route("/<int:user_id>/items/<int:item_id>")
@shopcart_ns.param("user_id", "The user ID")
@shopcart_ns.param("item_id", "The item ID")
class ShopcartItem(Resource):
    @shopcart_ns.doc("get_cart_item", summary="Get a specific item from a user's cart")
    @shopcart_ns.marshal_with(shopcart_item_model, code=200, description="Success")
    @shopcart_ns.response(404, "User or item not found")
    def get(self, user_id, item_id):
        """Returns a specific item from a user's shopcart."""
        resp, status = get_controller.get_cart_item_controller(user_id, item_id)
        return resp.get_json(force=True), status


# POST
@shopcart_ns.route("/<int:user_id>/add")
@shopcart_ns.param("user_id", "The user ID")
class ShopcartAdd(Resource):
    @shopcart_ns.doc(
        "add_to_or_create_cart", summary="Add item or update quantity in a user's cart"
    )
    @shopcart_ns.expect(shopcart_item_post_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=201, description="Item added or updated"
    )
    @shopcart_ns.response(400, "Invalid input")
    def post(self, user_id):
        """Add item to user's cart or update its quantity if it already exists."""
        response = post_controller.add_to_or_create_cart_controller(user_id)
        if isinstance(response, tuple):
            data, status_code, *rest = response
            headers = rest[0] if rest else {}
            return data.get_json(force=True), status_code, headers
        return response.get_json(force=True), response.status_code


@shopcart_ns.route("/<int:user_id>/products")
@shopcart_ns.param("user_id", "The user ID")
class AddProduct(Resource):
    @shopcart_ns.doc("add_product", summary="Add a product with validations")
    @shopcart_ns.expect(shopcart_product_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=201, description="Product added"
    )
    @shopcart_ns.response(400, "Bad request or validation error")
    def post(self, user_id):
        """Add a product with validations (stock, limits, etc)."""
        response = post_controller.add_product_to_cart_controller(user_id)
        if isinstance(response, tuple):
            data, status_code, *rest = response
            headers = rest[0] if rest else {}
            return data.get_json(force=True), status_code, headers
        return response.get_json(force=True), response.status_code


@shopcart_ns.route("/<int:user_id>/checkout")
@shopcart_ns.param("user_id", "The user ID")
class Checkout(Resource):
    @shopcart_ns.doc(
        "checkout_cart", summary="Finalize the cart and proceed to payment"
    )
    @shopcart_ns.response(200, "Checkout successful")
    @shopcart_ns.response(400, "Validation error")
    @shopcart_ns.response(500, "Internal server error")
    def post(self, user_id):
        """Checkout the cart and finalize payment."""
        response = post_controller.checkout_controller(user_id)
        if isinstance(response, tuple):
            data, status_code, *rest = response
            return data.get_json(force=True), status_code
        return response.get_json(force=True), response.status_code


# PUT + DELETE COMBINED
@shopcart_ns.route("/<int:user_id>")
@shopcart_ns.param("user_id", "The user ID")
class ShopcartModify(Resource):
    @shopcart_ns.doc("update_shopcart", summary="Update the user's entire cart")
    @shopcart_ns.expect(shopcart_item_list_model, validate=True)
    @shopcart_ns.marshal_list_with(
        shopcart_item_model, code=200, description="Cart updated"
    )
    @shopcart_ns.response(400, "Bad request")
    @shopcart_ns.response(404, "Shopcart not found")
    def put(self, user_id):
        """Update all items in a user's cart"""
        return put_controller.update_shopcart_controller(user_id)

    @shopcart_ns.doc("delete_shopcart", summary="Delete the entire user's cart")
    @shopcart_ns.response(204, "Cart deleted")
    @shopcart_ns.response(500, "Internal server error")
    def delete(self, user_id):
        """Delete all items from a user's cart"""
        return delete_controller.delete_shopcart_controller(user_id)


@shopcart_ns.route("/<int:user_id>/items/<int:item_id>")
@shopcart_ns.param("user_id", "The user ID")
@shopcart_ns.param("item_id", "The item ID")
class CartItemModify(Resource):
    @shopcart_ns.doc("update_cart_item", summary="Update a single item in the cart")
    @shopcart_ns.expect(quantity_only_model, validate=True)
    @shopcart_ns.marshal_with(
        shopcart_item_model, code=200, description="Item updated or removed"
    )
    @shopcart_ns.response(400, "Invalid input or negative quantity")
    @shopcart_ns.response(404, "Item or cart not found")
    def put(self, user_id, item_id):
        """Update the quantity of a specific item in the cart"""
        return put_controller.update_cart_item_controller(user_id, item_id)

    @shopcart_ns.doc("delete_cart_item", summary="Delete a specific item from the cart")
    @shopcart_ns.response(204, "Item deleted")
    @shopcart_ns.response(404, "Item not found in cart")
    @shopcart_ns.response(500, "Internal server error")
    def delete(self, user_id, item_id):
        """Delete a specific item from the user's cart"""
        return delete_controller.delete_shopcart_item_controller(user_id, item_id)
