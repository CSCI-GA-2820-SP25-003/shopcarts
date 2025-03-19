"""
Checkout controller logic for a shopcart service
"""

from flask import jsonify
from flask import current_app as app
from service.models import Shopcart, DataValidationError


def checkout_controller(user_id):
    """Finalize a user's cart and proceed with payment."""
    try:
        total_price = Shopcart.finalize_cart(user_id)
        return (
            jsonify(
                {
                    "message": f"Cart {user_id} checked out successfully",
                    "total_price": total_price,
                }
            ),
            200,
        )

    except DataValidationError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:  # pylint: disable=broad-except
        app.logger.error("Checkout error for user %s: %s", user_id, e)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
