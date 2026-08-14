"""
Create/refresh the automatic Oasis Plus member discount offer.

    python manage.py setup_membership_offer

An always-on Site offer whose custom condition only applies for active members,
giving them ``MEMBERSHIP_DISCOUNT_PERCENT`` off. Idempotent.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")
Range = get_model("offer", "Range")

CONDITION_PATH = "membership.models.MembershipCondition"
OFFER_NAME = "Oasis Plus member discount"


class Command(BaseCommand):
    help = "Set up the automatic member discount offer."

    @transaction.atomic
    def handle(self, *args, **options):
        percent = getattr(settings, "MEMBERSHIP_DISCOUNT_PERCENT", 5)

        rng, _ = Range.objects.get_or_create(
            slug="all-products",
            defaults={"name": "All products", "includes_all_products": True},
        )
        if not rng.includes_all_products:
            rng.includes_all_products = True
            rng.save()

        condition, _ = Condition.objects.get_or_create(proxy_class=CONDITION_PATH)

        benefit, _ = Benefit.objects.get_or_create(
            range=rng, type=Benefit.PERCENTAGE, value=percent
        )

        offer, created = ConditionalOffer.objects.get_or_create(
            name=OFFER_NAME,
            defaults={
                "description": "%d%% off every order for Oasis Plus members." % percent,
                "offer_type": ConditionalOffer.SITE,
                "condition": condition,
                "benefit": benefit,
            },
        )
        offer.condition = condition
        offer.benefit = benefit
        offer.offer_type = ConditionalOffer.SITE
        offer.status = ConditionalOffer.OPEN
        # Run before generic site offers so members always get their rate.
        offer.priority = 10
        offer.save()

        self.stdout.write(
            self.style.SUCCESS(
                "%s member offer: %d%% off (%s)."
                % ("Created" if created else "Updated", percent, OFFER_NAME)
            )
        )
