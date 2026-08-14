from django.test import RequestFactory, TestCase

from oscar.core.loading import get_model

from recommendations.templatetags.recommendation_tags import best_sellers, buy_again
from oasis.testutils import make_product, make_user, place_order

ProductRecord = get_model("analytics", "ProductRecord")


class BestSellersTests(TestCase):
    def test_ranked_by_purchases(self):
        p1 = make_product(title="Popular")
        p2 = make_product(title="Niche")
        ProductRecord.objects.create(product=p1, num_purchases=10)
        ProductRecord.objects.create(product=p2, num_purchases=2)
        result = best_sellers(8)
        self.assertEqual([p.title for p in result], ["Popular", "Niche"])

    def test_excludes_never_sold(self):
        make_product(title="Unsold")  # no ProductRecord
        self.assertEqual(best_sellers(8), [])


class BuyAgainTests(TestCase):
    def test_returns_user_purchases(self):
        buyer = make_user("buyer")
        product = make_product()
        place_order(buyer, product)
        rf = RequestFactory()
        req = rf.get("/")
        req.user = buyer
        self.assertIn(product, buy_again(req))

    def test_empty_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        rf = RequestFactory()
        req = rf.get("/")
        req.user = AnonymousUser()
        self.assertEqual(buy_again(req), [])
