from django.test import TestCase
from django.urls import reverse

from vendor.models import SellerFeedback
from vendor.templatetags.vendor_tags import seller_rating
from oasis.testutils import make_seller_product, make_user, partner_of, place_order


class SellerRatingTests(TestCase):
    def setUp(self):
        self.seller = make_user("seller")
        self.product = make_seller_product(self.seller, partner_name="Shop")
        self.partner = partner_of(self.product)

    def test_empty_rating(self):
        r = seller_rating(self.partner)
        self.assertEqual(r["count"], 0)
        self.assertIsNone(r["avg"])

    def test_aggregate_and_positive_pct(self):
        for score in (5, 4, 2):  # avg 3.67, 2 of 3 positive
            SellerFeedback.objects.create(
                partner=self.partner, user=make_user("u%d" % score), score=score
            )
        r = seller_rating(self.partner)
        self.assertEqual(r["count"], 3)
        self.assertEqual(r["positive_pct"], 67)


class LeaveFeedbackTests(TestCase):
    def setUp(self):
        self.buyer = make_user("buyer")
        self.seller = make_user("seller")
        self.product = make_seller_product(self.seller, partner_name="Shop")
        self.partner = partner_of(self.product)
        self.order = place_order(self.buyer, self.product)

    def test_buyer_can_rate_seller_from_order(self):
        self.client.force_login(self.buyer)
        self.client.post(
            reverse("vendor:leave-feedback", kwargs={"order_number": self.order.number, "code": self.partner.code}),
            {"score": "4", "comment": "Great"},
        )
        fb = SellerFeedback.objects.get(partner=self.partner, user=self.buyer)
        self.assertEqual(fb.score, 4)

    def test_cannot_rate_seller_not_in_order(self):
        other_product = make_seller_product(make_user("s2"), partner_name="Other")
        other_partner = partner_of(other_product)
        self.client.force_login(self.buyer)
        resp = self.client.get(
            reverse("vendor:leave-feedback", kwargs={"order_number": self.order.number, "code": other_partner.code})
        )
        self.assertEqual(resp.status_code, 403)
