from django.shortcuts import redirect 
from oscar.apps.checkout.views import PaymentDetailsView
from .momo import request_payment


class MomoPaymentDetailsView(PaymentDetailsView):
    def handle_payment(self, order_number, total, **kwargs):
        phone = self.request.POST.get('momo_phone')
        external_id = order_number
        payer_message = f"Order {order_number}"
        payee_note = "Thank you for shopping"
        reference_id, status_code, response = request_payment(
            amount=total.incl_tax,
            phone_number=phone,
            external_id=external_id,
            payer_message=payer_message,
            payee_note=payee_note,
        )

        if status_code != 202:
            raise Exception(f"Momo payment failed: {response}")
        
        # Store transaction reference in order's source
        self.add_payment_source(
            self.get_payment_source_model()(
                source_type = self.get_payment_source_type(),
                amount_allocated=total.incl_tax,
                reference=reference_id,
            )
        )
        self.add_payment_event('Authorised', total.incl_tax)


