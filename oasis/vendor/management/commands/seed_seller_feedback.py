"""
Seed example seller feedback (buyer ratings of sellers) so store pages, the
"Sold by" line and the seller dashboard show reputation data.

    python manage.py seed_seller_feedback           # rate sellers from existing orders
    python manage.py seed_seller_feedback --wipe     # delete all seller feedback first

For each order, each seller in it may receive one rating from that buyer
(Amazon-like J-curve, mostly 4-5). Idempotent per (seller, buyer, order).
Run with PYTHONIOENCODING=utf-8 on Windows.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from oscar.core.loading import get_model

Order = get_model("order", "Order")
Partner = get_model("partner", "Partner")

SCORE_POOL = [5, 5, 5, 5, 4, 4, 4, 3, 2, 1]
COMMENTS = {
    5: ["Fast delivery, item exactly as described.", "Great seller, will buy again!", "Smooth transaction, highly recommend.", ""],
    4: ["Good service, minor delay.", "Happy overall.", ""],
    3: ["Okay, took a while to arrive.", ""],
    2: ["Communication could be better.", ""],
    1: ["Item arrived damaged, poor response.", "Would not buy again."],
}


class Command(BaseCommand):
    help = "Seed example seller feedback from existing orders."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--seed", type=int, default=11)

    @transaction.atomic
    def handle(self, *args, **options):
        from vendor.models import SellerFeedback

        rng = random.Random(options["seed"])

        if options["wipe"]:
            n = SellerFeedback.objects.count()
            SellerFeedback.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted %d feedback row(s)." % n))

        existing = set(
            SellerFeedback.objects.values_list("partner_id", "user_id", "order_id")
        )

        created = 0
        for order in Order.objects.exclude(user=None).prefetch_related("lines"):
            partner_ids = {p for p in order.lines.values_list("partner_id", flat=True) if p}
            for pid in partner_ids:
                if (pid, order.user_id, order.id) in existing:
                    continue
                # not every buyer leaves feedback
                if rng.random() > 0.7:
                    continue
                score = rng.choice(SCORE_POOL)
                SellerFeedback.objects.create(
                    partner_id=pid,
                    user=order.user,
                    order=order,
                    score=score,
                    comment=rng.choice(COMMENTS[score]),
                )
                existing.add((pid, order.user_id, order.id))
                created += 1

        self.stdout.write(self.style.SUCCESS("Created %d seller feedback row(s)." % created))
