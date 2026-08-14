"""
Seed example customer reviews so the ratings UI (stars, average, histogram,
verified-purchase badges) has realistic data.

    python manage.py seed_reviews            # add reviews to seeded products
    python manage.py seed_reviews --all      # cover every product
    python manage.py seed_reviews --wipe     # delete all reviews first

Scores follow an Amazon-like J-curve (mostly 4-5). Reviewers who actually
ordered the product are used first, so some reviews show "Verified Purchase".
Idempotent: one review per (product, user); re-runs fill gaps only.
Run with PYTHONIOENCODING=utf-8 on Windows.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
ProductReview = get_model("reviews", "ProductReview")
Line = get_model("order", "Line")

try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
except Exception:  # pragma: no cover
    User = None

# Weighted score pool — skewed positive like a real marketplace.
SCORE_POOL = [5, 5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 2, 1]

TITLES = {
    5: ["Excellent!", "Exactly what I wanted", "Highly recommend", "Love it", "Best purchase"],
    4: ["Very good", "Happy with it", "Great value", "Solid choice", "Would buy again"],
    3: ["It's okay", "Decent", "Does the job", "Average", "Fair for the price"],
    2: ["Disappointed", "Not great", "Expected more", "Below par"],
    1: ["Would not recommend", "Poor quality", "Not worth it", "Very unhappy"],
}
BODIES = {
    5: [
        "Arrived quickly and works perfectly. Couldn't be happier.",
        "Great quality for the price — exceeded my expectations.",
        "Been using it for a while now and it's fantastic.",
    ],
    4: [
        "Really good overall, just a couple of minor niggles.",
        "Does what it says. Good value and fast delivery.",
        "Pleased with the purchase, would recommend to a friend.",
    ],
    3: [
        "It's fine for the price but nothing special.",
        "Works, but the quality could be a bit better.",
        "Average product — met the basic expectations.",
    ],
    2: [
        "Not quite what I hoped for. A bit underwhelming.",
        "Had some issues with it, wouldn't rush to buy again.",
    ],
    1: [
        "Stopped working almost immediately. Very disappointed.",
        "Poor quality and not worth the money.",
    ],
}


class Command(BaseCommand):
    help = "Seed example customer reviews across products."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Cover every product.")
        parser.add_argument("--wipe", action="store_true", help="Delete all reviews first.")
        parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        if options["wipe"]:
            n = ProductReview.objects.count()
            ProductReview.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted %d review(s)." % n))

        users = list(User.objects.filter(is_active=True)) if User else []
        if not users:
            self.stderr.write("No active users to author reviews.")
            return

        products = Product.objects.browsable()
        if not options["all"]:
            products = products.filter(upc__startswith="OASIS-")

        created = 0
        for product in products:
            existing_user_ids = set(
                product.reviews.values_list("user_id", flat=True)
            )

            # Buyers of this product go first -> they become "Verified Purchase".
            buyer_ids = list(
                Line.objects.filter(product=product)
                .exclude(order__user=None)
                .values_list("order__user_id", flat=True)
                .distinct()
            )
            buyers = [u for u in users if u.id in buyer_ids]
            others = [u for u in users if u.id not in buyer_ids]
            rng.shuffle(others)
            candidates = buyers + others

            target = rng.randint(3, 9)
            for user in candidates:
                if target <= 0:
                    break
                if user.id in existing_user_ids:
                    continue

                score = rng.choice(SCORE_POOL)
                ProductReview.objects.create(
                    product=product,
                    user=user,
                    score=score,
                    title=rng.choice(TITLES[score]),
                    body=rng.choice(BODIES[score]),
                    status=ProductReview.APPROVED,
                )
                existing_user_ids.add(user.id)
                created += 1
                target -= 1

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded %d review(s) across %d product(s)."
                % (created, products.count())
            )
        )
