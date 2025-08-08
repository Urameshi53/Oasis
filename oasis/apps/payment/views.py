# views.py
from django.shortcuts import redirect
from django.urls import reverse
from .paystack import initialize_payment, verify_payment
from django.views import View
from django.http import HttpResponse
from oscar.core.loading import get_class



class PaystackRedirectView(View):
    def get(self, request, *args, **kwargs):
        email = request.user.email
        amount = request.session.get('basket_total')  # store total earlier
        order_number = request.session.get('order_number')
        callback_url = request.build_absolute_uri(reverse('checkout:paystack-callback'))

        result = initialize_payment(email, amount, order_number, callback_url)

        if result['status']:
            return redirect(result['data']['authorization_url'])
        else:
            # Handle failure
            return redirect('checkout:payment-failed')

OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')

class PaystackCallbackView(OrderPlacementMixin, View):
    def get(self, request):
        reference = request.GET.get('reference')
        result = verify_payment(reference)

        if result['data']['status'] == 'success':
            # Process the order
            basket = self.request.basket
            order_number = request.session.get('order_number')
            total = basket.total_incl_tax

            # Save payment event and place order
            self.handle_payment(order_number, total)
            return self.place_order(
                order_number=order_number,
                basket=basket,
                total=total,
                shipping_address=self.get_shipping_address(basket),
                shipping_method=self.get_shipping_method(basket),
                billing_address=None,
                order_kwargs={}
            )
        else:
            return redirect('checkout:payment-failed')

class CustomPaymentDetailsView(PaymentDetailsView):
    def handle_payment(self, order_number, total, **kwargs):
        payment_method = self.request.session.get('payment_method')

        if payment_method == 'cod':
            return

        elif payment_method == 'paystack':
            self.request.session['basket_total'] = total.incl_tax
            self.request.session['order_number'] = order_number
            raise RedirectRequired(reverse('checkout:paystack-redirect'))

        else:
            raise ValueError("Unknown payment method")
