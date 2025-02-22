"""
Test Factory to make fake objects for testing
"""

import factory
from faker import Faker
from service.models import Shopcart

fake = Faker()

used_shopcart_pairs = set()


class ShopcartFactory(factory.Factory):
    """Creates fake Shopcart entries"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Shopcart

    @staticmethod
    def generate_unique_user_item():
        """Generate a unique (user_id, item_id) pair"""
        while True:
            user_id = fake.random_int(min=1, max=100)
            item_id = fake.random_int(min=1, max=100)

            if (user_id, item_id) not in used_shopcart_pairs:
                used_shopcart_pairs.add((user_id, item_id))
                return user_id, item_id

    description = factory.LazyFunction(lambda: fake.sentence())
    quantity = factory.LazyFunction(lambda: fake.random_int(min=1, max=50))
    price = factory.LazyFunction(lambda: round((fake.random_number(digits=5) / 10), 2))
    created_at = factory.LazyFunction(lambda: fake.date_time_this_decade())

    @factory.lazy_attribute
    def last_updated(self):
        return fake.date_time_between(start_date=self.created_at)

    @factory.post_generation
    def assign_unique_user_item(self, create, extracted, **kwargs):
        """Assigns a unique user_id and item_id after object creation"""
        self.user_id, self.item_id = ShopcartFactory.generate_unique_user_item()
