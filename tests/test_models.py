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
Test cases for Shopcart Model
"""

# pylint: disable=duplicate-code
import os
import logging
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import Shopcart, DataValidationError, db
from tests.factories import ShopcartFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  S H O P C A R T   M O D E L   B A S E   T E S T   C A S E
######################################################################
class ShopCartModelTestCase(TestCase):
    """Base Test Case for Shopcarts Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Shopcart).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()


######################################################################
#  S H O P C A R T   C R E A T I O N   T E S T   C A S E S
######################################################################
class TestShopCartCreation(ShopCartModelTestCase):
    """Test Cases for Shopcart Creation"""

    def test_create_a_shopcart(self):
        """It should create a shopcart entry and assert that it exists"""
        shopcart = Shopcart(
            user_id=1, item_id=2, description="Hello World!", quantity=1, price=3.0
        )
        self.assertEqual(str(shopcart), "<Shopcart user_id=1 item_id=2>")
        self.assertTrue(shopcart is not None)
        self.assertEqual(shopcart.user_id, 1)
        self.assertEqual(shopcart.item_id, 2)
        self.assertEqual(shopcart.description, "Hello World!")
        self.assertEqual(shopcart.quantity, 1)
        self.assertAlmostEqual(shopcart.price, 3.0)
        self.assertIsNone(shopcart.created_at)
        self.assertIsNone(shopcart.last_updated)

        manual_datetime = datetime.now(timezone.utc)
        shopcart = Shopcart(
            user_id=4,
            item_id=10,
            description="Goodbye World!",
            quantity=2,
            price=5.5,
            created_at=manual_datetime,
            last_updated=manual_datetime,
        )
        self.assertEqual(str(shopcart), "<Shopcart user_id=4 item_id=10>")
        self.assertTrue(shopcart is not None)
        self.assertEqual(shopcart.user_id, 4)
        self.assertEqual(shopcart.item_id, 10)
        self.assertEqual(shopcart.description, "Goodbye World!")
        self.assertEqual(shopcart.quantity, 2)
        self.assertAlmostEqual(shopcart.price, 5.5)
        self.assertEqual(shopcart.created_at, manual_datetime)
        self.assertEqual(shopcart.last_updated, manual_datetime)

    def test_add_a_shopcart(self):
        """It should Create a shopcart and add it to the database"""
        shopcarts = Shopcart.all()
        self.assertEqual(shopcarts, [])
        shopcart = Shopcart(
            user_id=1, item_id=2, description="Hello World!", quantity=1, price=3.0
        )
        self.assertTrue(shopcart is not None)
        self.assertEqual(shopcart.user_id, 1)
        self.assertEqual(shopcart.item_id, 2)
        self.assertEqual(shopcart.description, "Hello World!")
        self.assertEqual(shopcart.quantity, 1)
        self.assertAlmostEqual(shopcart.price, 3.0)
        self.assertIsNone(shopcart.created_at)
        self.assertIsNone(shopcart.last_updated)

        shopcart.create()
        self.assertIsNotNone(shopcart.created_at)
        self.assertIsNotNone(shopcart.last_updated)
        shopcarts = Shopcart.all()
        self.assertEqual(len(shopcarts), 1)

    def test_create_database_failure(self):
        """It should raise a DataValidationError when the database create fails"""
        shopcart = ShopcartFactory()

        patcher = patch(
            "service.models.db.session.commit", side_effect=Exception("DB error")
        )
        patcher.start()

        self.assertRaises(DataValidationError, shopcart.create)

        patcher.stop()


######################################################################
#  S H O P C A R T   V A L I D A T I O N   T E S T   C A S E S
######################################################################
class TestShopCartValidation(ShopCartModelTestCase):
    """Test Cases for Shopcart Validation"""

    def test_missing_user_id_and_item_id(self):
        """It should fail if both user_id and item_id are missing"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(description="Hello", quantity=1, price=3.0).create(),
        )

    def test_null_user_id(self):
        """It should fail if user_id is None"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=None, item_id=2, description="Hello", quantity=1, price=3.0
            ).create(),
        )

    def test_null_item_id(self):
        """It should fail if item_id is None"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=None, description="Hello", quantity=1, price=3.0
            ).create(),
        )

    def test_invalid_user_id(self):
        """It should fail if user_id is not an integer"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id="invalid", item_id=2, description="Hello", quantity=1, price=3.0
            ).create(),
        )

    def test_invalid_item_id(self):
        """It should fail if item_id is not an integer"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id="wrong", description="Hello", quantity=1, price=3.0
            ).create(),
        )

    def test_invalid_price_string(self):
        """It should fail if price is not a number"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description="Hello", quantity=1, price="abc"
            ).create(),
        )

    def test_negative_price(self):
        """It should fail if price is negative"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description="Hello", quantity=1, price=-5.0
            ).create(),
        )

    def test_excessive_decimal_price(self):
        """It should fail if price has more than two decimal places"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description="Hello", quantity=1, price=5.999
            ).create(),
        )

    def test_invalid_quantity_string(self):
        """It should fail if quantity is not an integer"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description="Hello", quantity="three", price=3.0
            ).create(),
        )

    def test_zero_quantity(self):
        """It should fail if quantity is zero or negative"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description="Hello", quantity=0, price=3.0
            ).create(),
        )

    def test_invalid_description(self):
        """It should fail if description is not a string"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1, item_id=2, description=12345, quantity=1, price=3.0
            ).create(),
        )

    def test_invalid_created_at_format(self):
        """It should fail if created_at is not in ISO format"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1,
                item_id=2,
                description="Hello",
                quantity=1,
                price=3.0,
                created_at="invalid_date",
            ).create(),
        )

    def test_invalid_last_updated_format(self):
        """It should fail if last_updated is not in ISO format"""
        self.assertRaises(
            ValueError,
            lambda: Shopcart(
                user_id=1,
                item_id=2,
                description="Hello",
                quantity=1,
                price=3.0,
                last_updated=["bad"],
            ).create(),
        )


######################################################################
#  S H O P C A R T   O P E R A T I O N S   T E S T   C A S E S
######################################################################
class TestShopCartOperations(ShopCartModelTestCase):
    """Test Cases for Shopcart Operations"""

    def test_read_a_shopcart(self):
        """It should Read a Shopcart entry"""
        shopcart = ShopcartFactory()
        logging.debug(shopcart)

        shopcart.create()

        self.assertIsNotNone(shopcart.user_id)
        self.assertIsNotNone(shopcart.item_id)

        found_shopcart = Shopcart.find(shopcart.user_id, shopcart.item_id)

        self.assertIsNotNone(found_shopcart)
        self.assertEqual(found_shopcart.user_id, shopcart.user_id)
        self.assertEqual(found_shopcart.item_id, shopcart.item_id)
        self.assertEqual(found_shopcart.description, shopcart.description)
        self.assertEqual(found_shopcart.quantity, shopcart.quantity)
        self.assertEqual(found_shopcart.price, shopcart.price)

    def test_update_no_user_id(self):
        """It should not Update a Shopcart with no user_id"""
        shopcart = ShopcartFactory()
        logging.debug(shopcart)

        shopcart.create()

        shopcart.user_id = None
        self.assertRaises(ValueError, shopcart.update)

    def test_update_no_item_id(self):
        """It should not Update a Shopcart with no item_id"""
        shopcart = ShopcartFactory()
        logging.debug(shopcart)

        shopcart.create()

        shopcart.item_id = None
        self.assertRaises(ValueError, shopcart.update)

    def test_update_a_shopcart(self):
        """It should Update a Shopcart entry"""
        shopcart = ShopcartFactory()
        logging.debug(shopcart)

        shopcart.create()
        logging.debug(shopcart)

        self.assertIsNotNone(shopcart.user_id)
        self.assertIsNotNone(shopcart.item_id)
        # Change it and save it
        shopcart.description = "Updated Description"
        original_user_id = shopcart.user_id
        original_item_id = shopcart.item_id
        shopcart.update()

        self.assertEqual(shopcart.user_id, original_user_id)
        self.assertEqual(shopcart.item_id, original_item_id)
        self.assertEqual(shopcart.description, "Updated Description")

        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        shopcarts = Shopcart.all()
        self.assertEqual(len(shopcarts), 1)
        self.assertEqual(shopcarts[0].user_id, original_user_id)
        self.assertEqual(shopcarts[0].item_id, original_item_id)
        self.assertEqual(shopcarts[0].description, "Updated Description")

    def test_update_database_failure(self):
        """It should raise a DataValidationError when the database update fails"""
        shopcart = ShopcartFactory()
        shopcart.create()

        patcher = patch(
            "service.models.db.session.commit", side_effect=Exception("DB error")
        )
        patcher.start()
        self.assertRaises(DataValidationError, shopcart.update)
        patcher.stop()

    def test_delete_a_shopcart(self):
        """It should Delete a Shopcart entry"""
        shopcart = ShopcartFactory()
        shopcart.create()

        self.assertEqual(len(Shopcart.all()), 1)
        # delete the shopcart and make sure it isn't in the database
        shopcart.delete()
        self.assertEqual(len(Shopcart.all()), 0)

    def test_delete_database_failure(self):
        """It should raise a DataValidationError when the database delete fails"""
        shopcart = ShopcartFactory()
        shopcart.create()

        patcher = patch(
            "service.models.db.session.commit", side_effect=Exception("DB error")
        )
        patcher.start()
        self.assertRaises(DataValidationError, shopcart.delete)
        patcher.stop()

    def test_list_all_shopcarts(self):
        """It should List all Shopcarts in the database"""
        shopcarts = Shopcart.all()
        self.assertEqual(shopcarts, [])

        # Create 5 Shopcarts
        for _ in range(5):
            shopcart = ShopcartFactory()
            shopcart.create()

        # Check if we get back 5 Shopcarts
        shopcarts = Shopcart.all()
        self.assertEqual(len(shopcarts), 5)


######################################################################
#  S H O P C A R T   S E R I A L I Z A T I O N   T E S T   C A S E S
######################################################################
class TestShopCartSerialization(ShopCartModelTestCase):
    """Test Cases for Shopcart Serialization"""

    def test_serialize_a_shopcart(self):
        """It should serialize a Shopcart"""
        shopcart = Shopcart(
            user_id=1,
            item_id=2,
            description="Test Item",
            quantity=3,
            price=12.99,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            last_updated=datetime(2024, 1, 2, 15, 30, 0),
        )
        data = shopcart.serialize()

        self.assertNotEqual(data, None)
        self.assertIn("user_id", data)
        self.assertEqual(data["user_id"], shopcart.user_id)
        self.assertIn("item_id", data)
        self.assertEqual(data["item_id"], shopcart.item_id)
        self.assertIn("description", data)
        self.assertEqual(data["description"], shopcart.description)
        self.assertIn("quantity", data)
        self.assertEqual(data["quantity"], shopcart.quantity)
        self.assertIn("price", data)
        self.assertEqual(
            data["price"], float(shopcart.price)
        )  # Ensure Decimal is converted to float
        self.assertIn("created_at", data)
        self.assertEqual(data["created_at"], shopcart.created_at.isoformat())
        self.assertIn("last_updated", data)
        self.assertEqual(data["last_updated"], shopcart.last_updated.isoformat())

    def test_deserialize_a_shopcart(self):
        """It should deserialize a Shopcart"""
        data = {
            "user_id": 1,
            "item_id": 2,
            "description": "Test Item",
            "quantity": 3,
            "price": 12.99,
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-02T15:30:00",
        }

        shopcart = Shopcart()
        shopcart.deserialize(data)

        self.assertNotEqual(shopcart, None)
        self.assertEqual(shopcart.user_id, data["user_id"])
        self.assertEqual(shopcart.item_id, data["item_id"])
        self.assertEqual(shopcart.description, data["description"])
        self.assertEqual(shopcart.quantity, data["quantity"])
        self.assertEqual(shopcart.price, data["price"])
        self.assertEqual(
            shopcart.created_at, datetime.fromisoformat(data["created_at"])
        )
        self.assertEqual(
            shopcart.last_updated, datetime.fromisoformat(data["last_updated"])
        )

    def test_deserialize_missing_data(self):
        """It should not deserialize a Shopcart with missing required fields"""
        data = {"user_id": 1, "description": "Test Item"}
        shopcart = Shopcart()
        self.assertRaises(DataValidationError, shopcart.deserialize, data)

    def test_deserialize_bad_price(self):
        """It should not deserialize a bad price attribute"""
        test_shopcart = {
            "user_id": 1,
            "item_id": 2,
            "description": "Test Item",
            "quantity": 3,
            "price": "invalid_price",
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-02T15:30:00",
        }
        shopcart = Shopcart()
        self.assertRaises(DataValidationError, shopcart.deserialize, test_shopcart)

    def test_deserialize_bad_quantity(self):
        """It should not deserialize a bad quantity attribute"""
        test_shopcart = {
            "user_id": 1,
            "item_id": 2,
            "description": "Test Item",
            "quantity": "three",
            "price": 12.99,
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-02T15:30:00",
        }
        shopcart = Shopcart()
        self.assertRaises(DataValidationError, shopcart.deserialize, test_shopcart)

    def test_deserialize_bad_created_at(self):
        """It should not deserialize a bad created_at format"""
        test_shopcart = {
            "user_id": 1,
            "item_id": 2,
            "description": "Test Item",
            "quantity": 3,
            "price": 12.99,
            "created_at": "invalid_date",
            "last_updated": "2024-01-02T15:30:00",
        }
        shopcart = Shopcart()
        self.assertRaises(DataValidationError, shopcart.deserialize, test_shopcart)

    def test_deserialize_bad_last_updated(self):
        """It should not deserialize a bad last_updated format"""
        test_shopcart = {
            "user_id": 1,
            "item_id": 2,
            "description": "Test Item",
            "quantity": 3,
            "price": 12.99,
            "created_at": "2024-01-01T12:00:00",
            "last_updated": ["bad"],
        }
        shopcart = Shopcart()
        self.assertRaises(DataValidationError, shopcart.deserialize, test_shopcart)


######################################################################
#  S H O P C A R T   Q U E R Y   T E S T   C A S E S
######################################################################
class TestShopCartQueries(ShopCartModelTestCase):
    """Test Cases for Shopcart Queries"""

    def test_find_shopcart(self):
        """It should Find a Shopcart entry by user_id and item_id"""
        shopcarts = ShopcartFactory.create_batch(5)
        for shopcart in shopcarts:
            shopcart.create()
        logging.debug(shopcarts)

        self.assertEqual(len(Shopcart.all()), 5)

        shopcart = Shopcart.find(shopcarts[1].user_id, shopcarts[1].item_id)

        self.assertIsNotNone(shopcart)
        self.assertEqual(shopcart.user_id, shopcarts[1].user_id)
        self.assertEqual(shopcart.item_id, shopcarts[1].item_id)
        self.assertEqual(shopcart.description, shopcarts[1].description)
        self.assertEqual(shopcart.quantity, shopcarts[1].quantity)
        self.assertEqual(shopcart.price, shopcarts[1].price)
        self.assertEqual(shopcart.created_at, shopcarts[1].created_at)

    def test_find_by_user_id(self):
        """It should Find Shopcarts by user_id"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        user_id = shopcarts[0].user_id
        count = len([sc for sc in shopcarts if sc.user_id == user_id])

        found = Shopcart.find_by_user_id(user_id)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.user_id, user_id)

    def test_find_by_description(self):
        """It should Find Shopcarts by description"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        description = shopcarts[0].description
        count = len([sc for sc in shopcarts if sc.description == description])

        found = Shopcart.find_by_description(description)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.description, description)

    def test_find_by_quantity(self):
        """It should Find Shopcarts by quantity"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        quantity = shopcarts[0].quantity
        count = len([sc for sc in shopcarts if sc.quantity == quantity])

        found = Shopcart.find_by_quantity(quantity)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.quantity, quantity)

    def test_find_by_price(self):
        """It should Find Shopcarts by price"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        price = shopcarts[0].price
        count = len([sc for sc in shopcarts if sc.price == price])

        found = Shopcart.find_by_price(price)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.price, price)

    def test_find_by_created_at(self):
        """It should Find Shopcarts by created_at"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        created_at = shopcarts[0].created_at
        count = len([sc for sc in shopcarts if sc.created_at == created_at])

        found = Shopcart.find_by_created_at(created_at)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.created_at, created_at)

    def test_find_by_last_updated(self):
        """It should Find Shopcarts by last_updated"""
        shopcarts = ShopcartFactory.create_batch(10)
        for shopcart in shopcarts:
            shopcart.create()

        last_updated = shopcarts[0].last_updated
        count = len([sc for sc in shopcarts if sc.last_updated == last_updated])

        found = Shopcart.find_by_last_updated(last_updated)

        self.assertEqual(len(found), count)
        for shopcart in found:
            self.assertEqual(shopcart.last_updated, last_updated)

    def test_build_filter_conditions_in(self):
        """It should generate conditions for 'in' operator"""
        filters = {"user_id": {"operator": "in", "value": [1, 2, 3]}}
        conditions = Shopcart._build_filter_conditions(filters)

        # Ensure the IN condition exists
        self.assertEqual(len(conditions), 1)
        condition_str = str(conditions[0])

        # Check that the SQLAlchemy query contains the correct structure
        self.assertIn("shopcart.user_id IN", condition_str)
        self.assertIn("POSTCOMPILE", condition_str)

    def test_find_by_ranges_direct(self):
        """It should directly test find_by_ranges to ensure coverage"""
        # Create 3 entries
        sc1 = ShopcartFactory(price=15.0, quantity=2)
        sc2 = ShopcartFactory(price=45.0, quantity=4)
        sc3 = ShopcartFactory(price=55.0, quantity=6)

        for sc in [sc1, sc2, sc3]:
            sc.create()

        filters = {
            "min_price": 10,
            "max_price": 50,  # Should exclude sc3
            "min_qty": 1,
            "max_qty": 5,  # Should exclude sc3
        }

        results = Shopcart.find_by_ranges(filters)

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(10 <= float(result.price) <= 50)
            self.assertTrue(1 <= result.quantity <= 5)
