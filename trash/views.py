from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView
from oasis.momo.momo_client import MoMoAPI

class PaymentDetailsView(CorePaymentDetailsView):
    def handle_payment(self, order_number, total, **kwargs):
        # Get phone number from custom form or request
        phone = self.request.POST.get('phone')
        momo = MoMoAPI()
        paid = momo.request_to_pay(amount=total.incl_tax, phone=phone, external_id=order_number)

        if not paid:
            raise Exception("Payment failed or not accepted")

from django.http import JsonResponse

@csrf_exempt
def momo_callback(request):
    # Parse and validate callback data
    data = json.loads(request.body)
    print(data)
    return JsonResponse({"status": "received"})
