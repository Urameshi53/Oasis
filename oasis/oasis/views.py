# yourapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from oscar.apps.order.models import Order
import requests

@csrf_exempt
def paystack_callback(request):
    reference = request.GET.get('reference')
    if not reference:
        return HttpResponse("No reference", status=400)

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=headers)
    result = response.json()

    if result['status'] and result['data']['status'] == 'success':
        try:
            order = Order.objects.get(number=reference)
            order.set_status('Paid')
            return HttpResponse("Payment verified")
        except Order.DoesNotExist:
            return HttpResponse("Order not found", status=404)
    return HttpResponse("Payment failed", status=400)
