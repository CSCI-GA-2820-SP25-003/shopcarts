from flask_restx import Namespace, fields


shopcart_ns = Namespace("shopcarts", description="Operations on user shopcarts")


# === RESTX Models ===

# A single item in the cart
shopcart_item_model = shopcart_ns.model(
    "ShopcartItem",
    {
        "user_id": fields.Integer(description="User ID"),
        "item_id": fields.Integer(description="Item ID"),
        "description": fields.String(description="Description of the item"),
        "quantity": fields.Integer(description="Quantity of the item"),
        "price": fields.Float(description="Price per unit"),
        "created_at": fields.String(description="Timestamp when item was added"),
        "last_updated": fields.String(
            description="Timestamp when item was last updated"
        ),
    },
)


# Cart response for a single user
user_cart_model = shopcart_ns.model(
    "UserCart",
    {
        "user_id": fields.Integer(description="User ID"),
        "items": fields.List(
            fields.Nested(shopcart_item_model), description="List of items"
        ),
    },
)

# Response: list of user carts
multi_cart_response = shopcart_ns.model(
    "ShopcartList",
    {"shopcarts": fields.List(fields.Nested(user_cart_model))},
)


shopcart_item_list_model = shopcart_ns.model(
    "ShopcartItemList",
    {"items": fields.List(fields.Nested(shopcart_item_model), required=True)},
)

quantity_only_model = shopcart_ns.model(
    "QuantityOnly",
    {
        "quantity": fields.Integer(
            required=True, min=0, description="New quantity for the item"
        )
    },
)

# === Parsers for POST ===
shopcart_item_post_model = shopcart_ns.model(
    "CartItem",
    {
        "item_id": fields.Integer(required=True),
        "description": fields.String(required=True),
        "quantity": fields.Integer(required=False, default=1),
        "price": fields.Float(required=True),
    },
)

shopcart_product_model = shopcart_ns.model(
    "CartProduct",
    {
        "product_id": fields.Integer(required=True),
        "quantity": fields.Integer(required=True),
        "name": fields.String(required=True),
        "price": fields.Float(required=True),
        "stock": fields.Integer(required=True),
        "purchase_limit": fields.Integer(required=True),
    },
)
