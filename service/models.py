"""
Models for Shopcart

All of the models are stored in this module

Models
------
Shopcart - A Shopcart representing items a user has added for potential purchase

Attributes:
-----------
user_id (integer) - the unique ID of the user who owns the cart
item_id (integer) - the unique ID of the item in the cart
description (string) - a brief description of the item
quantity (integer) - the number of this item in the cart
price (decimal) - the price per unit of the item
created_at (datetime) - the timestamp when the item was added to the cart
last_updated (datetime) - the timestamp of the most recent update to the item in the cart
"""

import math
import logging
from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Shopcart(db.Model):
    """
    Class that represents a shopcart entry
    """

    ##################################################
    # Table Schema
    ##################################################
    user_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    last_updated = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )

    def validate(self):
        """Validates that the data in the Shopcarts entry meets certain requirements"""
        # Check required fields
        required_fields = {"user_id": self.user_id, "item_id": self.item_id}
        for field, value in required_fields.items():
            if value is None:
                raise ValueError(f"{field} must not be null.")

        # Type validation
        type_checks = {
            "user_id": (self.user_id, int),
            "item_id": (self.item_id, int),
            "price": (self.price, (float, int, Decimal)),
            "description": (self.description, str),
            "quantity": (self.quantity, int),
            "created_at": (self.created_at, (datetime, type(None))),
            "last_updated": (self.last_updated, (datetime, type(None))),
        }

        for field, (value, expected_type) in type_checks.items():
            if not isinstance(value, expected_type):
                raise ValueError(f"{field} must be of type {expected_type}.")

        # Specific value constraints
        if self.price < 0:
            raise ValueError("Price cannot be less than 0.")

        if Decimal(str(self.price)).as_tuple().exponent < -2:
            raise ValueError("Price cannot have more than 2 decimal places.")

        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

    def __repr__(self):
        return f"<Shopcart user_id={self.user_id} item_id={self.item_id}>"

    def create(self):
        """
        Creates a shopcart entry to the database
        """
        self.validate()
        logger.info(
            "Creating entry user_id: '%s', item_id: '%s'", self.user_id, self.item_id
        )
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a Shopcarts to the database
        """
        self.validate()
        logger.info("Saving user_id: '%s', item_id: '%s'", self.user_id, self.item_id)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a Shopcarts from the data store"""
        logger.info("Deleting user_id: '%s', item_id: '%s'", self.user_id, self.item_id)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Shopcart entry into a dictionary"""
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "description": self.description,
            "quantity": self.quantity,
            "price": float(self.price),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

    def deserialize(self, data):
        """
        Deserializes a Shopcart entry from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.user_id = int(data["user_id"])
            self.item_id = int(data["item_id"])
            self.description = str(data["description"])
            self.quantity = int(data["quantity"])
            self.price = float(data["price"])
            if "created_at" in data:
                self.created_at = datetime.fromisoformat(data["created_at"])

            if "last_updated" in data:
                self.last_updated = datetime.fromisoformat(data["last_updated"])

            self.validate()

        except KeyError as error:
            raise DataValidationError(
                "Invalid Shopcarts: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Shopcarts: body of request contained bad or no data "
                + str(error)
            ) from error
        except ValueError as error:
            raise DataValidationError("Invalid data format: " + str(error)) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Shopcarts in the database"""
        logger.info("Processing all Shopcarts")
        return cls.query.all()

    @classmethod
    def find(cls, user_id, item_id):
        """Finds a Shopcart entry by user_id and item_id

        :param user_id: the id of the user to find
        :type user_id: int
        :param item_id: the id of the item to find
        :type item_id: int

        :return: an instance with the user_id and item_id, or None if not found
        :rtype: Shopcart

        """
        logger.info(
            "Processing lookup for user_id=%s and item_id=%s ...", user_id, item_id
        )
        return cls.query.get((user_id, item_id))

    @classmethod
    def find_by_user_id(cls, user_id):
        """Finds a Shopcarts by user_id"""
        logger.info("Processing lookup for user_id %s ...", user_id)
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def find_by_description(cls, description):
        """Returns all Shopcarts with the given description

        :param description: the description of the Shopcarts you want to match
        :type description: str

        :return: a collection of Shopcart entries with the given description
        :rtype: list
        """
        logger.info("Processing lookup for description: %s ...", description)
        return cls.query.filter_by(description=description).all()

    @classmethod
    def find_by_quantity(cls, quantity):
        """Returns all Shopcarts with the given quantity

        :param quantity: the quantity of the Shopcart items to match
        :type quantity: int

        :return: a collection of Shopcart entries with the specified quantity
        :rtype: list
        """
        logger.info("Processing lookup for quantity: %s ...", quantity)
        return cls.query.filter_by(quantity=quantity).all()

    @classmethod
    def find_by_price(cls, price):
        """Returns all Shopcarts with the given price

        :param price: the price of the Shopcart items to match
        :type price: float

        :return: a collection of Shopcart entries with the specified price
        :rtype: list
        """
        logger.info("Processing lookup for price: %s ...", price)
        return cls.query.filter_by(price=price).all()

    @classmethod
    def find_by_created_at(cls, created_at):
        """Returns all Shopcarts created at the specified datetime

        :param created_at: the timestamp when the Shopcart was created
        :type created_at: datetime

        :return: a collection of Shopcart entries created at the given datetime
        :rtype: list
        """
        logger.info("Processing lookup for created_at: %s ...", created_at)
        return cls.query.filter_by(created_at=created_at).all()

    @classmethod
    def find_by_last_updated(cls, last_updated):
        """Returns all Shopcarts last updated at the specified datetime

        :param last_updated: the timestamp when the Shopcart was last updated
        :type last_updated: datetime

        :return: a collection of Shopcart entries last updated at the given datetime
        :rtype: list
        """
        logger.info("Processing lookup for last_updated: %s ...", last_updated)
        return cls.query.filter_by(last_updated=last_updated).all()

    @classmethod
    def find_by_ranges(cls, filters=None):
        """Finds all shopcart items based on optional ranges"""
        logger.info("Finding items with dynamic filters")
        filters = filters or {}

        min_price = filters.get("min_price", 0)
        max_price = filters.get("max_price", math.inf)

        min_qty = filters.get("min_qty", 0)
        max_qty = filters.get("max_qty", math.inf)

        min_date = filters.get("min_date", datetime(1970, 1, 1))
        max_date = filters.get("max_date", datetime(3000, 1, 1))

        min_update = filters.get("min_update", datetime(1970, 1, 1))
        max_update = filters.get("max_update", datetime(3000, 1, 1))

        return cls.query.filter(
            cls.price >= min_price,
            cls.price <= max_price,
            cls.quantity >= min_qty,
            cls.quantity <= max_qty,
            cls.created_at >= min_date,
            cls.created_at <= max_date,
            cls.last_updated >= min_update,
            cls.last_updated <= max_update,
        ).all()

    @classmethod
    def _apply_price_range_filters(cls, query, filters):
        """Apply price range filters to the query."""
        if 'price_min' in filters:
            query = query.filter(cls.price >= filters['price_min'])
        if 'price_max' in filters:
            query = query.filter(cls.price <= filters['price_max'])
        return query

    @classmethod
    def find_by_user_id_with_filter(cls, user_id, filters=None):
        """
        Finds and returns all Shopcart entries for a specific user with optional filters
        Args:
            user_id (int): the user ID
            filters (dict, optional): Optional filters to apply
                - price_min: Minimum price threshold
        - price_max: Maximum price threshold
        Returns:
            List[Shopcart]: List of Shopcart objects that match the user ID and filters
        """
        query = cls.query.filter(cls.user_id == user_id)
        if not filters:
            return query.all()
        # Apply price range filters (these are special cases)
        query = cls._apply_price_range_filters(query, filters)
        # Apply operator-based filters
        operator_filters = {k: v for k, v in filters.items()
                            if k not in ['price_min', 'price_max']
                            and isinstance(v, dict)
                            and 'operator' in v and 'value' in v}

        if operator_filters:
            conditions = cls._build_filter_conditions(operator_filters)
            for condition in conditions:
                query = query.filter(condition)

        return query.all()

    @classmethod
    def _build_filter_conditions(cls, filters):
        """Creates filter conditions from filter dict

        This is a private helper method to reduce complexity
        """
        conditions = []

        # Dictionary mapping field types to conversion functions
        type_converters = {
            "price": float,
            "quantity": int,
            "item_id": int,
            "created_at": datetime.fromisoformat,
            "last_updated": datetime.fromisoformat,
        }

        for field, condition in filters.items():
            model_attr = getattr(cls, field)
            operator = condition["operator"]
            value = condition["value"]

            # Convert value if needed
            if field in type_converters:
                try:
                    value = type_converters[field](value)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid value for {field}: {value}") from exc

            # Map operators to conditions
            if operator == "eq":
                conditions.append(model_attr == value)
            elif operator == "lt":
                conditions.append(model_attr < value)
            elif operator == "lte":
                conditions.append(model_attr <= value)
            elif operator == "gt":
                conditions.append(model_attr > value)
            elif operator == "gte":
                conditions.append(model_attr >= value)

        return conditions

    @classmethod
    def finalize_cart(cls, user_id):
        """Finalizes the cart for the given user_id"""
        items = cls.find_by_user_id(user_id)
        if not items:
            raise DataValidationError(f"No cart found for user {user_id}")

        # Calculate total price
        total_price = 0.0
        for item in items:
            total_price += float(item.price) * item.quantity

        if total_price == 0.0:
            raise DataValidationError("Cart is empty. Nothing to checkout.")

        # Remove each item from the database to represent "checked out"
        for item in items:
            item.delete()

        return total_price
