"""
Test cases for shopcart filtering and queries
"""

from datetime import datetime
from service.models import Shopcart, db
from service.controllers.get_controller import apply_filter
from service.common import status
from .test_routes import TestShopcartService


class TestShopcartFiltering(TestShopcartService):
    """Test cases for filtering and queries on shopcarts"""

    def test_filter_shopcarts_by_exact_created_at(self):
        """It should filter shopcarts by exact created_at date"""
        self._populate_shopcarts(count=2, user_id=1)

        # Get the created_at timestamp from the first item
        shopcart = Shopcart.query.first()
        created_date = shopcart.created_at.strftime("%Y-%m-%d")

        resp = self.client.get(f"/shopcarts?created_at={created_date}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertGreater(len(data), 0)

        for cart in data:
            for item in cart["items"]:
                self.assertEqual(item["created_at"][:10], created_date)

    def test_filter_shopcarts_by_created_at_range(self):
        """It should filter shopcarts using created_at range queries"""
        self._populate_shopcarts(count=5)

        # Test range query (e.g., created_at >= some date)
        date_query = "2023-09-01"
        resp = self.client.get(f"/shopcarts?created_at=~gte~{date_query}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        for cart in data:
            for item in cart["items"]:
                self.assertGreaterEqual(
                    datetime.strptime(item["created_at"][:10], "%Y-%m-%d"),
                    datetime.strptime(date_query, "%Y-%m-%d"),
                )

    def test_filter_shopcarts_by_multiple_created_at(self):
        """It should filter shopcarts using multiple created_at values"""
        self._populate_shopcarts(count=5)

        # Fetch two created_at values
        created_dates = [
            shopcart.created_at.strftime("%Y-%m-%d")
            for shopcart in Shopcart.query.limit(2).all()
        ]
        date_query = ",".join(created_dates)

        resp = self.client.get(f"/shopcarts?created_at={date_query}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertGreater(len(data), 0)

        for cart in data:
            for item in cart["items"]:
                self.assertIn(item["created_at"][:10], created_dates)

    def test_filter_shopcarts_by_multiple_user_ids(self):
        """It should filter shopcarts using multiple user_id values"""
        self._populate_shopcarts(count=2, user_id=1)
        self._populate_shopcarts(count=2, user_id=2)

        # Get shopcarts for user_id=1 or user_id=2
        resp = self.client.get("/shopcarts?user_id=1,2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertGreater(len(data), 0)

        for shopcart in data:
            self.assertIn(
                shopcart["user_id"], [1, 2]
            )  # Ensure only these users are returned

    def test_filter_shopcarts_no_results(self):
        """It should return an empty list if no shopcarts match the filter"""

        # 🔹 Ensure database is empty
        db.session.query(Shopcart).delete()
        db.session.commit()

        # 🔹 Query for shopcarts that don't exist
        resp = self.client.get("/shopcarts?user_id=9999")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data, [], "Expected empty list but got data")

    def test_get_shopcarts_invalid_operator(self):
        """It should return 400 Bad Request for an invalid operator in filtering"""
        resp = self.client.get("/shopcarts?price=~invalid~100")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid filter value: ~invalid~100", data["error"])

    def test_apply_filter_invalid_value(self):
        """It should raise a ValueError for an invalid filter value"""
        with self.assertRaises(ValueError) as context:
            apply_filter(Shopcart.price, int, "invalid-number")

        self.assertIn("Invalid filter value", str(context.exception))

    def test_parse_datetime_invalid_format(self):
        """It should raise a ValueError for an invalid date format"""

        # 🔹 Send an invalid date format to trigger the exception
        resp = self.client.get("/shopcarts?created_at=invalid-date")

        # 🔹 Ensure the response is 400 Bad Request
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 🔹 Verify error message
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid date format", data["error"])
