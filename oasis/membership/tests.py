from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from oscar.apps.partner.strategy import Selector
from oscar.core.loading import get_class, get_model

from membership.models import Membership, user_is_member
from oasis.testutils import make_product, make_user

Basket = get_model("basket", "Basket")
Applicator = get_class("offer.applicator", "Applicator")


class MembershipModelTests(TestCase):
    def setUp(self):
        self.user = make_user("mem")

    def test_active_when_not_expired(self):
        m = Membership.objects.create(user=self.user, expires_at=timezone.now() + timedelta(days=5))
        self.assertTrue(m.active)
        self.assertTrue(user_is_member(self.user))

    def test_inactive_when_expired(self):
        Membership.objects.create(user=self.user, expires_at=timezone.now() - timedelta(days=1))
        self.assertFalse(user_is_member(self.user))

    def test_inactive_when_cancelled(self):
        Membership.objects.create(
            user=self.user, is_active=False, expires_at=timezone.now() + timedelta(days=5)
        )
        self.assertFalse(user_is_member(self.user))

    def test_anonymous_is_not_member(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(user_is_member(AnonymousUser()))


class MemberDiscountTests(TestCase):
    """The custom offer condition must gate the discount on membership."""

    def setUp(self):
        call_command("setup_membership_offer")
        self.product = make_product(price="200.00")

    def _discount_for(self, user):
        Basket.objects.filter(owner=user).delete()
        basket = Basket.objects.create(owner=user, status="Open")
        basket.strategy = Selector().strategy(user=user)
        basket.add_product(self.product, quantity=1)
        Applicator().apply(basket, user=user)
        return basket.total_discount

    def test_non_member_gets_no_discount(self):
        user = make_user("plain")
        self.assertEqual(self._discount_for(user), 0)

    def test_member_gets_five_percent(self):
        user = make_user("gold")
        Membership.objects.create(user=user, expires_at=timezone.now() + timedelta(days=30))
        # 5% of 200 = 10
        self.assertEqual(self._discount_for(user), 10)


class MembershipViewTests(TestCase):
    def setUp(self):
        self.user = make_user("joiner")
        self.client.force_login(self.user)

    def test_join_activates_membership(self):
        self.assertFalse(user_is_member(self.user))
        self.client.post(reverse("membership:join"))
        self.assertTrue(user_is_member(self.user))

    def test_cancel_deactivates(self):
        self.client.post(reverse("membership:join"))
        self.client.post(reverse("membership:cancel"))
        self.assertFalse(user_is_member(self.user))

    def test_page_renders(self):
        self.assertEqual(self.client.get(reverse("membership:home")).status_code, 200)
