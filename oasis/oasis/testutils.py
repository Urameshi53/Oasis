"""
Shared fixtures/helpers for the Oasis test suites. Uses Oscar's test factories
to spin up products, sellers, buyers and orders with minimal boilerplate.
"""

from decimal import Decimal as D

from django.contrib.auth import get_user_model

from oscar.apps.partner.strategy import Selector
from oscar.core.loading import get_model
from oscar.test.factories import create_order, create_product

User = get_user_model()
Basket = get_model("basket", "Basket")


def make_user(username, **kwargs):
    kwargs.setdefault("email", "%s@example.com" % username)
    return User.objects.create_user(username=username, password="pw12345", **kwargs)


def make_product(title="Widget", price="100.00", partner_name="Acme Store",
                 num_in_stock=10, partner_users=None):
    """A saleable product with a stockrecord (and optionally a linked seller)."""
    return create_product(
        title=title,
        price=D(str(price)),
        partner_name=partner_name,
        num_in_stock=num_in_stock,
        partner_users=partner_users,
    )


def make_seller_product(seller_user, title="Seller Widget", price="100.00",
                        partner_name="Seller Shop"):
    """A product whose partner has ``seller_user`` linked (so seller flows work)."""
    return make_product(
        title=title, price=price, partner_name=partner_name,
        partner_users=[seller_user],
    )


def place_order(user, product, quantity=1, number=None):
    """Create a placed order containing ``product`` for ``user``."""
    basket = Basket.objects.create(owner=user)
    basket.strategy = Selector().strategy(user=user)
    basket.add_product(product, quantity=quantity)
    return create_order(basket=basket, user=user, number=number)


def partner_of(product):
    return product.stockrecords.first().partner
