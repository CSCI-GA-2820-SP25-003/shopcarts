######################################################################
# Test Cases for Shopcart Namespace Endpoints
######################################################################
"""Test suite for endpoints defined in shopcarts_namespace.py"""

from datetime import datetime
from unittest.mock import patch, Mock

from service import create_app
from service.common import status
from service.controllers.shopcarts_namespace import (
    ShopcartList,
    ShopcartByUser,
    ShopcartItem,
    ShopcartAdd,
    AddProduct,
    ShopcartModify,
    CartItemModify,
)

from .test_routes import TestShopcartService

app = create_app()


class TestShopcartNamespaceGet(TestShopcartService):
    """Tests for endpoints in shopcart_namespace.py"""

    def _mock_json_response(self, payload, status_code):
        mock_resp = Mock()
        mock_resp.get_json.return_value = payload
        mock_resp.status_code = status_code

        if isinstance(payload, list) and payload:
            mock_resp.user_id = payload[0].get("user_id", 1)
        elif isinstance(payload, dict):
            mock_resp.user_id = payload.get("user_id", 1)
        else:
            mock_resp.user_id = 1

        return mock_resp

    def test_shopcart_add_post(self):
        """Test adding item to cart returns 201 Created."""
        with app.test_request_context():
            with patch(
                "service.controllers.post_controller.add_to_or_create_cart_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response(
                    [
                        {
                            "item_id": 1,
                            "user_id": 1,
                            "description": "apple",
                            "quantity": 3,
                            "price": 2.99,
                            "created_at": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat(),
                        }
                    ],
                    status.HTTP_201_CREATED,
                )
                mock_ctrl.return_value = (
                    mock_resp,
                    status.HTTP_201_CREATED,
                    {"Location": "/shopcarts/1"},
                )
                resource = ShopcartAdd()
                _, code, _ = resource.post(user_id=1)
                self.assertEqual(code, status.HTTP_201_CREATED)

    def test_add_product_post(self):
        """Test adding a validated product returns 201 Created."""
        with app.test_request_context():
            with patch(
                "service.controllers.post_controller.add_product_to_cart_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response(
                    [
                        {
                            "item_id": 1,
                            "user_id": 1,
                            "description": "banana",
                            "quantity": 5,
                            "price": 1.99,
                            "created_at": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat(),
                        }
                    ],
                    status.HTTP_201_CREATED,
                )
                mock_ctrl.return_value = (
                    mock_resp,
                    status.HTTP_201_CREATED,
                    {"Location": "/shopcarts/1"},
                )
                resource = AddProduct()
                _, code, _ = resource.post(user_id=1)
                self.assertEqual(code, status.HTTP_201_CREATED)

    def test_shopcart_modify_delete(self):
        """Test deleting a user's cart returns 204 No Content."""
        with app.test_request_context():
            with patch(
                "service.controllers.delete_controller.delete_shopcart_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response({}, status.HTTP_204_NO_CONTENT)
                mock_ctrl.return_value = mock_resp, status.HTTP_204_NO_CONTENT
                resource = ShopcartModify()
                _, code = resource.delete(user_id=1)
                self.assertEqual(code, status.HTTP_204_NO_CONTENT)

    def test_cart_item_modify_delete(self):
        """Test deleting a specific item from a user's cart returns 204 No Content."""
        with app.test_request_context():
            with patch(
                "service.controllers.delete_controller.delete_shopcart_item_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response({}, status.HTTP_204_NO_CONTENT)
                mock_ctrl.return_value = mock_resp, status.HTTP_204_NO_CONTENT
                resource = CartItemModify()
                _, code = resource.delete(user_id=1, item_id=1)
                self.assertEqual(code, status.HTTP_204_NO_CONTENT)

    def test_list_all_shopcarts_with_params(self):
        """Test shopcart listing with filter parameters returns 200 OK."""
        with app.test_request_context("/shopcarts/?min_price=1&max_price=10"):
            with patch(
                "service.controllers.get_controller.get_shopcarts_controller"
            ) as mock_get:
                mock_resp = self._mock_json_response(
                    [{"user_id": 1}], status.HTTP_200_OK
                )
                mock_get.return_value = mock_resp, status.HTTP_200_OK
                resource = ShopcartList()
                resp = resource.get()
                self.assertEqual(resp[1], status.HTTP_200_OK)

    def test_user_shopcart_with_filters(self):
        """Test retrieving a user's shopcart with filters returns 200 OK."""
        with app.test_request_context("/shopcarts/1?min_quantity=1&max_quantity=10"):
            with patch(
                "service.controllers.get_controller.get_user_shopcart_controller"
            ) as mock_get:
                mock_resp = self._mock_json_response(
                    {"user_id": 1, "items": []}, status.HTTP_200_OK
                )
                mock_get.return_value = mock_resp, status.HTTP_200_OK
                resource = ShopcartByUser()
                resp = resource.get(user_id=1)
                self.assertEqual(resp[1], status.HTTP_200_OK)

    def test_cart_item_get_with_params(self):
        """Test retrieving a specific item returns 200 OK."""
        with app.test_request_context("/shopcarts/1/items/1"):
            with patch(
                "service.controllers.get_controller.get_cart_item_controller"
            ) as mock_get:
                item = {
                    "item_id": 1,
                    "user_id": 1,
                    "description": "apple",
                    "quantity": 3,
                    "price": 2.99,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat(),
                }
                mock_resp = self._mock_json_response(item, status.HTTP_200_OK)
                mock_get.return_value = mock_resp, status.HTTP_200_OK
                resource = ShopcartItem()
                resp = resource.get(user_id=1, item_id=1)
                self.assertEqual(resp[1], status.HTTP_200_OK)

    def test_shopcart_add_post_two_tuple(self):
        """Test fallback two-tuple return path of ShopcartAdd."""
        with app.test_request_context():
            with patch(
                "service.controllers.post_controller.add_to_or_create_cart_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response({}, status.HTTP_201_CREATED)
                mock_ctrl.return_value = mock_resp
                resource = ShopcartAdd()
                resp = resource.post(user_id=1)
                self.assertEqual(resp[1], status.HTTP_201_CREATED)
                self.assertEqual(resp[2], {})

    def test_add_product_post_two_tuple(self):
        """Test fallback two-tuple return path of AddProduct."""
        with app.test_request_context():
            with patch(
                "service.controllers.post_controller.add_product_to_cart_controller"
            ) as mock_ctrl:
                mock_resp = self._mock_json_response({}, status.HTTP_201_CREATED)
                mock_ctrl.return_value = mock_resp
                resource = AddProduct()
                resp = resource.post(user_id=1)
                self.assertEqual(resp[1], status.HTTP_201_CREATED)
