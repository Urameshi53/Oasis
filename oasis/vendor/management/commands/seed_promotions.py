"""
Seed example promotions: a couple of coupon codes and an automatic site offer,
so the basket coupon box and the Deals page have something real to show.

    python manage.py seed_promotions          # create/update sample promos
    python manage.py seed_promotions --wipe    # remove them first

Run with PYTHONIOENCODING=utf-8 on Windows.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")
Range = get_model("offer", "Range")
Voucher = get_model("voucher", "Voucher")


class Command(BaseCommand):
    help = "Seed example vouchers and a site offer."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true")

    def _all_products_range(self):
        rng, _ = Range.objects.get_or_create(
            slug="all-products",
            defaults={"name": "All products", "includes_all_products": True},
        )
        if not rng.includes_all_products:
            rng.includes_all_products = True
            rng.save()
        return rng

    def _make_voucher(self, code, name, benefit_type, value, rng):
        benefit, _ = Benefit.objects.get_or_create(
            range=rng, type=benefit_type, value=value
        )
        condition, _ = Condition.objects.get_or_create(
            range=rng, type=Condition.COUNT, value=1
        )
        offer, _ = ConditionalOffer.objects.get_or_create(
            name="Voucher: %s" % name,
            defaults={
                "offer_type": ConditionalOffer.VOUCHER,
                "condition": condition,
                "benefit": benefit,
            },
        )
        offer.condition = condition
        offer.benefit = benefit
        offer.offer_type = ConditionalOffer.VOUCHER
        offer.status = ConditionalOffer.OPEN
        offer.save()

        voucher, created = Voucher.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "usage": Voucher.MULTI_USE,
                "start_datetime": timezone.now() - timedelta(days=1),
                "end_datetime": timezone.now() + timedelta(days=365),
            },
        )
        voucher.offers.add(offer)
        return voucher, created

    @transaction.atomic
    def handle(self, *args, **options):
        if options["wipe"]:
            Voucher.objects.filter(code__in=["WELCOME10", "SAVE20", "STUDENT5"]).delete()
            ConditionalOffer.objects.filter(name__startswith="Voucher:").delete()
            ConditionalOffer.objects.filter(name="Student Special").delete()
            self.stdout.write(self.style.WARNING("Wiped sample promotions."))

        rng = self._all_products_range()

        made = []
        v1, _ = self._make_voucher("WELCOME10", "Welcome 10% off", Benefit.PERCENTAGE, 10, rng)
        v2, _ = self._make_voucher("SAVE20", "GHS 20 off your order", Benefit.FIXED, 20, rng)
        made += [v1.code, v2.code]

        # An automatic site-wide offer (no code needed) — 5% student discount.
        benefit, _ = Benefit.objects.get_or_create(range=rng, type=Benefit.PERCENTAGE, value=5)
        condition, _ = Condition.objects.get_or_create(range=rng, type=Condition.COUNT, value=2)
        site_offer, _ = ConditionalOffer.objects.get_or_create(
            name="Student Special",
            defaults={
                "description": "5% off when you buy 2 or more items.",
                "offer_type": ConditionalOffer.SITE,
                "condition": condition,
                "benefit": benefit,
            },
        )
        site_offer.status = ConditionalOffer.OPEN
        site_offer.offer_type = ConditionalOffer.SITE
        site_offer.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Promotions ready: coupons %s + site offer '%s'."
                % (", ".join(made), site_offer.name)
            )
        )
