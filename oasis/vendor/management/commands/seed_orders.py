"""
Seed example placed orders so verified-purchase badges, best-sellers, order
history and the analytics dashboard have real data.

    python manage.py seed_orders            # create example orders
    python manage.py seed_orders --wipe     # delete previously seeded orders first
    python manage.py seed_orders --count 60 # roughly how many orders to aim for

Strategy: first turn a sample of existing reviews into real purchases (so those
reviews show "Verified Purchase"), then add extra multi-item orders for spread.
Orders are placed via Oscar's OrderCreator, which fires ``order_placed`` — so
each also gets a rider Delivery + vendor VendorSale row. Idempotent per
(user, product): a user won't be given a second order for a product they've
already ordered. Run with PYTHONIOENCODING=utf-8 on Windows.
"""

import random
from datetime import timedelta
from decimal import Decimal as D

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from oscar.apps.order.utils import OrderCreator
from oscar.apps.partner.strategy import Selector
from oscar.apps.shipping.methods import Free
from oscar.core.loading import get_class, get_model

Product = get_model("catalogue", "Product")
ProductReview = get_model("reviews", "ProductReview")
Basket = get_model("basket", "Basket")
ShippingAddress = get_model("order", "ShippingAddress")
Country = get_model("address", "Country")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
OrderTotalCalculator = get_class("checkout.calculators", "OrderTotalCalculator")

SEED_PREFIX = "SEED-"

HOSTELS = ["Pentagon", "Evandy", "TF", "Africa Hall", "Unity Hall", "Katanga"]
LOCATIONS = ["Legon", "KNUST", "UCC", "Ashesi", "UPSA"]


class Command(BaseCommand):
    help = "Seed example placed orders (verified purchases + best-seller spread)."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true", help="Delete seeded orders first.")
        parser.add_argument("--count", type=int, default=70, help="Approx number of orders.")
        parser.add_argument("--seed", type=int, default=7, help="RNG seed.")

    def _country(self):
        c = Country.objects.filter(iso_3166_1_a2="GH").first() or Country.objects.first()
        return c

    def _address(self, user, rng):
        return ShippingAddress(
            first_name=user.first_name or user.get_username(),
            last_name=user.last_name or "Student",
            line1="%s Hall, Room %d" % (rng.choice(HOSTELS), rng.randint(1, 320)),
            line4=rng.choice(LOCATIONS),
            postcode="",
            country=self._country(),
            phone_number="+23324%07d" % rng.randint(0, 9999999),
            hostel=rng.choice(HOSTELS),
            room_number=str(rng.randint(1, 320)),
            location=rng.choice(LOCATIONS),
        )

    def _place(self, user, products, rng, when):
        """Build a basket for `products` and place an order. Returns Order or None."""
        strategy = Selector().strategy(user=user)
        basket = Basket()
        basket.strategy = strategy
        for p in products:
            if p.stockrecords.exists():
                basket.add_product(p, quantity=1)
        if basket.is_empty:
            return None

        shipping_method = Free()
        shipping_charge = shipping_method.calculate(basket)
        order_total = OrderTotalCalculator().calculate(basket, shipping_charge)

        number = "%s%d" % (SEED_PREFIX, rng.randint(10_000_000, 99_999_999))
        status = rng.choice(["Delivered", "Delivered", "Shipped", "Pending"])
        address = self._address(user, rng)
        address.save()
        order = OrderCreator().place_order(
            basket=basket,
            total=order_total,
            shipping_method=shipping_method,
            shipping_charge=shipping_charge,
            user=user,
            shipping_address=address,
            order_number=number,
            status=status,
        )
        # Backdate for realistic analytics/history.
        Order.objects.filter(pk=order.pk).update(date_placed=when)
        return order

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])
        now = timezone.now()

        if options["wipe"]:
            qs = Order.objects.filter(number__startswith=SEED_PREFIX)
            n = qs.count()
            qs.delete()
            self.stdout.write(self.style.WARNING("Wiped %d seeded order(s)." % n))

        # (user, product) pairs that already have an order line — never duplicate.
        existing = set(
            Line.objects.values_list("order__user_id", "product_id")
        )

        created = 0
        target = options["count"]

        # 1) Turn a sample of reviews into verified purchases.
        reviews = list(
            ProductReview.objects.exclude(user=None).select_related("product", "user")
        )
        rng.shuffle(reviews)
        for review in reviews:
            if created >= target:
                break
            key = (review.user_id, review.product_id)
            if key in existing:
                continue
            if not review.product.stockrecords.exists():
                continue
            when = now - timedelta(days=rng.randint(1, 90), hours=rng.randint(0, 23))
            order = self._place(review.user, [review.product], rng, when)
            if order:
                existing.add(key)
                created += 1

        # 2) Extra multi-item orders for best-seller spread.
        users = [u for u in {r.user for r in reviews}] or []
        sellable = list(Product.objects.browsable().filter(stockrecords__isnull=False).distinct())
        while created < target and users and sellable:
            user = rng.choice(users)
            picks = rng.sample(sellable, k=min(rng.randint(1, 3), len(sellable)))
            picks = [p for p in picks if (user.id, p.id) not in existing]
            if not picks:
                continue
            when = now - timedelta(days=rng.randint(1, 90), hours=rng.randint(0, 23))
            order = self._place(user, picks, rng, when)
            if order:
                for p in picks:
                    existing.add((user.id, p.id))
                created += 1

        self.stdout.write(
            self.style.SUCCESS("Placed %d seeded order(s)." % created)
        )
