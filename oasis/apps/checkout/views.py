import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView
from oscar.apps.payment.models import Source, SourceType

logger = logging.getLogger("oscar.checkout")


class PaymentDetailsView(CorePaymentDetailsView):
    """
    Marketplace-aware payment step.

    On order placement a payment ``Source`` is recorded. When a Paystack secret
    key is configured, the buyer is then redirected to Paystack to pay, and the
    transaction carries a per-vendor *split* so each seller's share settles to
    their subaccount (see ``vendor.payments``). Without a key (e.g. local dev),
    the order is simply marked settled so checkout still completes.
    """

    def _paystack_enabled(self):
        return bool(getattr(settings, "PAYSTACK_SECRET_KEY", ""))

    def handle_payment(self, order_number, total, **kwargs):
        source_type, _ = SourceType.objects.get_or_create(name="Paystack")
        source = Source(
            source_type=source_type,
            currency=total.currency,
            amount_allocated=total.incl_tax,
            reference=order_number,
        )
        if self._paystack_enabled():
            # Funds are captured after redirect; mark as authorised for now.
            self.add_payment_event("Authorised", total.incl_tax, reference=order_number)
        else:
            # No live gateway configured — treat as settled (simplified flow).
            source.amount_debited = total.incl_tax
            self.add_payment_event("Settled", total.incl_tax, reference=order_number)
        self.add_payment_source(source)

    def handle_successful_order(self, order):
        # If Paystack is live, redirect the buyer to pay with a per-vendor split.
        if self._paystack_enabled() and order.total_incl_tax > 0:
            from vendor.payments import initialize_split_payment

            callback_url = self.request.build_absolute_uri(reverse("paystack-callback"))
            try:
                result = initialize_split_payment(
                    order.email, order, order.number, callback_url
                )
            except Exception:
                logger.exception("Paystack initialise failed for order %s", order.number)
                result = {"status": False}

            if result.get("status"):
                self.request.session["checkout_order_id"] = order.id
                self.checkout_session.flush()
                return HttpResponseRedirect(result["data"]["authorization_url"])
            # If initialisation failed, fall through to the normal thank-you page
            # so the order isn't lost; it can be reconciled/paid manually.

        return super().handle_successful_order(order)
