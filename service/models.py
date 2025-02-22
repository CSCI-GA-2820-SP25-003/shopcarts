"""
Models for Shopcart

All of the models are stored in this module
"""

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

        if self.user_id is None:
            raise ValueError("user_id must not be null.")

        if self.item_id is None:
            raise ValueError("item_id must not be null.")

        if not isinstance(self.user_id, int):
            raise ValueError("user_id must be an integer.")

        if not isinstance(self.item_id, int):
            raise ValueError("item_id must be an integer.")

        if not isinstance(self.price, (float, int, Decimal)):
            raise ValueError("Price must be a float or integer.")

        if self.price < 0:
            raise ValueError("Price cannot be less than 0")

        price_decimal = Decimal(str(self.price)).as_tuple()

        if price_decimal.exponent < -2:
            raise ValueError("Price cannot have more than 2 decimal places.")

        if not isinstance(self.description, str):
            raise ValueError("Description must be a string.")

        if not isinstance(self.quantity, int):
            raise ValueError("Quantity must be an integer.")

        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

        if self.created_at is not None and not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime object or None.")

        if self.last_updated is not None and not isinstance(
            self.last_updated, datetime
        ):
            raise ValueError("last_updated must be a datetime object or None.")

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

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
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
        """Finds a Shopcart entry by user_id and item_id"""
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
