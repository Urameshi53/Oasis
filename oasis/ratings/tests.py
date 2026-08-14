from django.test import TestCase

from oscar.core.loading import get_model

from ratings.templatetags.rating_tags import (
    is_verified_purchase,
    rating_breakdown,
    star_icons,
)
from oasis.testutils import make_product, make_user, place_order

ProductReview = get_model("reviews", "ProductReview")


class StarIconsTests(TestCase):
    def test_full_and_half_stars(self):
        html = star_icons(4.5)
        self.assertEqual(html.count("bi-star-fill"), 4)
        self.assertEqual(html.count("bi-star-half"), 1)

    def test_zero(self):
        html = star_icons(0)
        self.assertEqual(html.count("bi-star-fill"), 0)
        self.assertEqual(html.count("bi-star"), 5)  # bi-star matches empty stars

    def test_handles_none(self):
        # Should not raise
        self.assertIn("stars", star_icons(None))


class RatingBreakdownTests(TestCase):
    def test_breakdown_percentages(self):
        product = make_product()
        for i, score in enumerate((5, 5, 3)):
            ProductReview.objects.create(
                product=product, user=make_user("reviewer%d" % i),
                score=score, status=ProductReview.APPROVED,
            )
        rows = {r["score"]: r for r in rating_breakdown(product)}
        self.assertEqual(rows[5]["count"], 2)
        self.assertEqual(rows[5]["pct"], 67)
        self.assertEqual(rows[3]["count"], 1)


class VerifiedPurchaseTests(TestCase):
    def test_verified_when_user_ordered_product(self):
        buyer = make_user("buyer")
        product = make_product()
        place_order(buyer, product)
        review = ProductReview.objects.create(
            product=product, user=buyer, score=5, status=ProductReview.APPROVED
        )
        self.assertTrue(is_verified_purchase(review))

    def test_not_verified_without_order(self):
        product = make_product()
        review = ProductReview.objects.create(
            product=product, user=make_user("nope"), score=5, status=ProductReview.APPROVED
        )
        self.assertFalse(is_verified_purchase(review))
