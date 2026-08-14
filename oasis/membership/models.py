"""
"Oasis Plus" — a Prime-style membership.

A member gets an automatic discount on every order, wired through Oscar's offer
engine via a custom ``MembershipCondition`` (an offer that only applies when the
basket owner is an active member). Billing is out of scope here: joining
activates a 30-day membership immediately (a real deployment would settle the
fee through Paystack recurring).
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from oscar.apps.offer import models as offer_models


class Membership(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership"
    )
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    #: What the member pays per period (informational — no billing here).
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="GHS")

    def __str__(self):
        return f"Oasis Plus: {self.user} ({'active' if self.active else 'inactive'})"

    @property
    def active(self):
        return self.is_active and self.expires_at and self.expires_at > timezone.now()

    def renew(self, days=30):
        base = self.expires_at if (self.expires_at and self.expires_at > timezone.now()) else timezone.now()
        self.expires_at = base + timedelta(days=days)
        self.is_active = True
        self.save(update_fields=["expires_at", "is_active"])


def user_is_member(user):
    """True if the user currently holds an active Oasis Plus membership."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    m = Membership.objects.filter(user=user).first()
    return bool(m and m.active)


class MembershipCondition(offer_models.Condition):
    """
    Offer condition satisfied only when the basket's owner is an active Oasis
    Plus member. Drives the automatic member discount.
    """

    class Meta:
        proxy = True

    name = "Basket owner is an Oasis Plus member"

    def is_satisfied(self, offer, basket):
        return user_is_member(getattr(basket, "owner", None))

    def is_partially_satisfied(self, offer, basket):
        return False

    def get_upsell_message(self, offer, basket):
        return "Join Oasis Plus to save on every order."

    def consume_items(self, offer, basket, affected_lines):
        # A membership gate consumes no basket items.
        return
