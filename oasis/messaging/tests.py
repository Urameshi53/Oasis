from django.test import TestCase
from django.urls import reverse

from messaging.models import Message, MessageThread
from oasis.testutils import make_seller_product, make_user, partner_of


class MessagingTests(TestCase):
    def setUp(self):
        self.buyer = make_user("buyer")
        self.seller = make_user("seller")
        self.product = make_seller_product(self.seller, partner_name="Shop")
        self.partner = partner_of(self.product)

    def _contact(self, body="Hello?"):
        self.client.force_login(self.buyer)
        self.client.post(
            reverse("messaging:contact", kwargs={"code": self.partner.code}) + "?product=%d" % self.product.pk,
            {"body": body, "product": str(self.product.pk)},
        )
        return MessageThread.objects.get(buyer=self.buyer, partner=self.partner)

    def test_contact_creates_thread_and_notifies_unread(self):
        thread = self._contact()
        self.assertEqual(thread.messages.count(), 1)
        # seller has 1 unread, buyer 0
        self.assertEqual(thread.unread_count_for(self.seller), 1)
        self.assertEqual(thread.unread_count_for(self.buyer), 0)

    def test_reply_and_read_tracking(self):
        thread = self._contact()
        # seller opens the thread -> buyer's message marked read
        self.client.force_login(self.seller)
        self.client.get(reverse("messaging:thread", args=[thread.pk]))
        self.assertEqual(thread.unread_count_for(self.seller), 0)
        # seller replies -> buyer now has 1 unread
        self.client.post(reverse("messaging:thread", args=[thread.pk]), {"body": "Yes!"})
        self.assertEqual(thread.unread_count_for(self.buyer), 1)

    def test_outsider_gets_403(self):
        thread = self._contact()
        self.client.force_login(make_user("stranger"))
        resp = self.client.get(reverse("messaging:thread", args=[thread.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_cannot_message_own_store(self):
        self.client.force_login(self.seller)
        self.client.post(
            reverse("messaging:contact", kwargs={"code": self.partner.code}),
            {"body": "hi"},
        )
        self.assertFalse(MessageThread.objects.filter(buyer=self.seller).exists())
