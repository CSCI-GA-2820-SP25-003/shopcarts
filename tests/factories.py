import factory
from faker import Faker
from service.models import Shopcart

fake = Faker()

used_shopcart_pairs = set()


class ShopcartFactory(factory.Factory):
    """Creates fake Shopcart entries"""

    class Meta:
        model = Shopcart

    user_id = None
    description = factory.LazyFunction(lambda: fake.sentence())
    quantity = factory.LazyFunction(lambda: fake.random_int(min=1, max=50))
    price = factory.LazyFunction(lambda: round((fake.random_number(digits=5) / 10), 2))
    created_at = factory.LazyFunction(lambda: fake.date_time_this_decade())

    @factory.lazy_attribute
    def last_updated(self):
        return fake.date_time_between(start_date=self.created_at)

    @staticmethod
    def generate_unique_user_item(user_id=None):
        """Generate a unique (user_id, item_id) pair"""
        while True:
            # If no user_id was provided, generate one.
            if user_id is None:
                user_id = fake.random_int(min=1, max=100)
            item_id = fake.random_int(min=1, max=100)
            if (user_id, item_id) not in used_shopcart_pairs:
                used_shopcart_pairs.add((user_id, item_id))
                return user_id, item_id

    @factory.post_generation
    def assign_unique_user_item(self, create, extracted, **kwargs):
        """
        Assigns a unique user_id and item_id after object creation.
        If a specific user_id was provided when calling the factory,
        it will be used.
        """

        provided_user_id = self.user_id
        self.user_id, self.item_id = ShopcartFactory.generate_unique_user_item(
            user_id=provided_user_id
        )


def mock_product(
    product_id=111,
    name="Test Product",
    stock=10,
    purchase_limit=None,
    price=9.99,
    quantity=1,
):
    return {
        "product_id": product_id,
        "name": name,
        "stock": stock,
        "purchase_limit": purchase_limit,
        "price": price,
        "quantity": quantity,
    }
