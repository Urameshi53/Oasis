import json

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from oscar.apps.partner.strategy import Selector
from oscar.core.loading import get_class, get_model

from oasis.testutils import make_product, make_user, place_order

Basket = get_model("basket", "Basket")
Voucher = get_model("voucher", "Voucher")
Applicator = get_class("offer.applicator", "Applicator")


class WishlistToggleTests(TestCase):
    def setUp(self):
        self.user = make_user("shopper")
        self.product = make_product()
        self.client.force_login(self.user)

    def test_toggle_adds_then_removes(self):
        url = reverse("wishlist-toggle", args=[self.product.pk])
        r1 = json.loads(self.client.post(url).content)
        self.assertTrue(r1["in_wishlist"])
        self.assertEqual(r1["count"], 1)
        r2 = json.loads(self.client.post(url).content)
        self.assertFalse(r2["in_wishlist"])
        self.assertEqual(r2["count"], 0)

    def test_get_not_allowed(self):
        resp = self.client.get(reverse("wishlist-toggle", args=[self.product.pk]))
        self.assertEqual(resp.status_code, 405)


class OrderAccessTests(TestCase):
    def setUp(self):
        self.buyer = make_user("buyer")
        self.product = make_product()
        self.order = place_order(self.buyer, self.product)

    def test_owner_can_view_tracking_and_invoice(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("order-track", args=[self.order.number])).status_code, 200)
        self.assertEqual(self.client.get(reverse("order-invoice", args=[self.order.number])).status_code, 200)

    def test_other_user_gets_404(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(reverse("order-track", args=[self.order.number])).status_code, 404)
        self.assertEqual(self.client.get(reverse("order-invoice", args=[self.order.number])).status_code, 404)


class CouponTests(TestCase):
    def setUp(self):
        call_command("seed_promotions")
        self.user = make_user("buyer")
        self.product = make_product(price="100.00")

    def test_percentage_voucher_applies(self):
        basket = Basket.objects.create(owner=self.user, status="Open")
        basket.strategy = Selector().strategy(user=self.user)
        basket.add_product(self.product, quantity=1)
        basket.vouchers.add(Voucher.objects.get(code="WELCOME10"))
        Applicator().apply(basket, user=self.user)
        self.assertEqual(basket.total_discount, 10)  # 10% of 100
