from django.test import TestCase
from django.urls import reverse

from returns.models import ReturnLine, ReturnRequest
from returns.utils import can_return_order, returnable_qty
from oasis.testutils import make_seller_product, make_user, partner_of, place_order


class ReturnEligibilityTests(TestCase):
    def setUp(self):
        self.buyer = make_user("buyer")
        self.product = make_seller_product(make_user("seller"), price="50.00")
        self.order = place_order(self.buyer, self.product, quantity=2)

    def test_owner_can_return_recent_order(self):
        self.assertTrue(can_return_order(self.buyer, self.order))

    def test_other_user_cannot_return(self):
        self.assertFalse(can_return_order(make_user("stranger"), self.order))

    def test_returnable_qty_decrements_after_request(self):
        line = self.order.lines.first()
        self.assertEqual(returnable_qty(line), 2)
        rr = ReturnRequest.objects.create(order=self.order, user=self.buyer, reason="other")
        ReturnLine.objects.create(return_request=rr, order_line=line, quantity=1)
        self.assertEqual(returnable_qty(line), 1)


class ReturnFlowTests(TestCase):
    def setUp(self):
        self.buyer = make_user("buyer")
        self.seller = make_user("seller")
        self.product = make_seller_product(self.seller, price="100.00", partner_name="Shop")
        self.order = place_order(self.buyer, self.product, quantity=1)
        self.line = self.order.lines.first()

    def _create_request(self):
        self.client.force_login(self.buyer)
        self.client.post(
            reverse("returns:create", args=[self.order.number]),
            {"reason": "defective", "line_%d" % self.line.id: "1", "qty_%d" % self.line.id: "1"},
        )
        return ReturnRequest.objects.get(order=self.order)

    def test_create_computes_refund(self):
        rr = self._create_request()
        self.assertEqual(rr.status, ReturnRequest.REQUESTED)
        self.assertEqual(rr.expected_refund(), 100)

    def test_seller_can_manage_but_stranger_cannot(self):
        rr = self._create_request()
        self.assertTrue(rr.can_be_managed_by(self.seller))
        self.assertFalse(rr.can_be_managed_by(make_user("nobody")))

    def test_approve_then_refund_restocks(self):
        rr = self._create_request()
        sr = self.line.stockrecord
        start_stock = sr.num_in_stock
        rr.approve()
        rr.mark_refunded()
        rr.refresh_from_db()
        sr.refresh_from_db()
        self.assertEqual(rr.status, ReturnRequest.REFUNDED)
        self.assertEqual(rr.refund_amount, 100)
        self.assertEqual(sr.num_in_stock, start_stock + 1)

    def test_action_view_rejects_non_manager(self):
        rr = self._create_request()
        self.client.force_login(make_user("intruder"))
        resp = self.client.post(reverse("returns:action", args=[rr.pk]), {"action": "approve"})
        self.assertEqual(resp.status_code, 403)
        rr.refresh_from_db()
        self.assertEqual(rr.status, ReturnRequest.REQUESTED)
