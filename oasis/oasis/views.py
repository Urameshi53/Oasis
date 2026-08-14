# yourapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.db.models import Q
from oscar.apps.order.models import Order
import requests
from oscar.apps.catalogue.models import Product
from rest_framework import permissions, viewsets
from .serializers import ProductSerializer
from apps.payment.paystack import verify_payment
from oscar.apps.customer.views import AccountRegistrationView
from .forms import RegistrationForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView


class DealsView(TemplateView):
    """Public 'Today's deals' page — automatic site offers + coupon codes."""

    template_name = "oscar/offer/deals.html"

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from oscar.core.loading import get_model

        ConditionalOffer = get_model("offer", "ConditionalOffer")
        Voucher = get_model("voucher", "Voucher")
        now = timezone.now()

        ctx = super().get_context_data(**kwargs)
        ctx["site_offers"] = ConditionalOffer.objects.filter(
            offer_type=ConditionalOffer.SITE, status=ConditionalOffer.OPEN
        ).select_related("benefit")
        ctx["vouchers"] = [
            v
            for v in Voucher.objects.prefetch_related("offers", "offers__benefit")
            if v.is_active(now)
        ]
        return ctx


class OrderInvoiceView(LoginRequiredMixin, DetailView):
    """A printable invoice / receipt for the buyer's own order."""

    template_name = "oscar/customer/order/invoice.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Order, number=self.kwargs["order_number"], user=self.request.user
        )

    def get_context_data(self, **kwargs):
        from django.conf import settings

        ctx = super().get_context_data(**kwargs)
        order = self.object
        paid = (order.status or "").lower() == "paid" or order.sources.filter(
            amount_debited__gt=0
        ).exists()
        ctx["paid"] = paid
        ctx["shop_name"] = getattr(settings, "OSCAR_SHOP_NAME", "Oasis")
        return ctx


from django.views.decorators.http import require_POST


@require_POST
def wishlist_toggle(request, product_pk):
    """
    Add/remove a product from the user's default wishlist and return JSON
    ``{in_wishlist, count}``. Powers the heart button on product cards.
    Creates a wishlist on first use.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    from oscar.core.loading import get_model

    WishList = get_model("wishlists", "WishList")
    Line = get_model("wishlists", "Line")

    product = get_object_or_404(Product, pk=product_pk)
    wishlist = request.user.wishlists.first() or request.user.wishlists.create()

    lines = wishlist.lines.filter(product=product)
    if lines.exists():
        lines.delete()
        in_wishlist = False
    else:
        wishlist.add(product)
        in_wishlist = True

    count = Line.objects.filter(wishlist__owner=request.user).values("product_id").distinct().count()
    return JsonResponse({"in_wishlist": in_wishlist, "count": count})


class OrderTrackingView(LoginRequiredMixin, DetailView):
    """
    Amazon-style "track your order" page for the buyer.

    Joins Oscar's order state with the rider ``Delivery`` lifecycle into a
    single visual timeline (placed -> paid -> rider assigned -> picked up ->
    delivered). Scoped to the logged-in user's own orders only.
    """

    template_name = "oscar/customer/order/order_track.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Order, number=self.kwargs["order_number"], user=self.request.user
        )

    def _is_paid(self, order):
        if (order.status or "").lower() == "paid":
            return True
        return order.sources.filter(amount_debited__gt=0).exists()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = self.object
        delivery = getattr(order, "delivery", None)
        paid = self._is_paid(order)

        d_status = getattr(delivery, "status", None)
        cancelled = d_status == "cancelled"

        # Progress rank of the delivery lifecycle for marking steps complete.
        rank = {"claimed": 1, "picked_up": 2, "delivered": 3}.get(d_status, 0)

        steps = [
            {
                "key": "placed",
                "label": "Order placed",
                "desc": "We've received your order.",
                "icon": "bi-bag-check",
                "done": True,
                "at": order.date_placed,
            },
            {
                "key": "paid",
                "label": "Payment confirmed",
                "desc": "Your payment has been confirmed."
                if paid
                else "Waiting for payment confirmation.",
                "icon": "bi-credit-card",
                "done": paid,
                "at": None,
            },
            {
                "key": "assigned",
                "label": "Rider assigned",
                "desc": "A rider has picked up your delivery job."
                if rank >= 1
                else "Finding a rider for your delivery.",
                "icon": "bi-person-badge",
                "done": rank >= 1,
                "at": getattr(delivery, "claimed_at", None),
            },
            {
                "key": "on_the_way",
                "label": "On the way",
                "desc": "Your rider has your order and is heading over."
                if rank >= 2
                else "Your order will be picked up soon.",
                "icon": "bi-bicycle",
                "done": rank >= 2,
                "at": getattr(delivery, "picked_up_at", None),
            },
            {
                "key": "delivered",
                "label": "Delivered",
                "desc": "Your order has been delivered. Enjoy!"
                if rank >= 3
                else "Delivery in progress.",
                "icon": "bi-house-check",
                "done": rank >= 3,
                "at": getattr(delivery, "delivered_at", None),
            },
        ]

        # The current step is the last completed one (or the first if none).
        current_index = 0
        for i, step in enumerate(steps):
            if step["done"]:
                current_index = i

        ctx.update(
            {
                "delivery": delivery,
                "steps": steps,
                "current_index": current_index,
                "cancelled": cancelled,
                "is_paid": paid,
                "rider": getattr(delivery, "rider", None),
            }
        )
        return ctx


class RegisterView(AccountRegistrationView):
    """Registration that also collects the customer's first and last name."""

    form_class = RegistrationForm


@csrf_exempt
def paystack_callback(request):
    """
    Paystack redirects the buyer here after payment. We verify the transaction
    and, on success, mark the order paid and send the buyer to the thank-you
    page. The per-vendor split is applied by Paystack at charge time; the local
    VendorSale ledger was already created when the order was placed.
    """
    reference = request.GET.get('reference')
    if not reference:
        return HttpResponse("No reference", status=400)

    result = verify_payment(reference)

    if result.get('status') and result['data']['status'] == 'success':
        try:
            order = Order.objects.get(number=reference)
        except Order.DoesNotExist:
            return HttpResponse("Order not found", status=404)
        try:
            order.set_status('Paid')
        except Exception:
            pass  # status pipeline may not define 'Paid'; payment still verified
        return redirect(reverse('checkout:thank-you'))
    return HttpResponse("Payment failed", status=400)


'''
from rest_framework.decorators import api_view
from rest_framework.response import Response
from oscar.apps.catalogue.models import Product
from .serializers import ProductSerializer


@api_view(["GET"])
def product_list(request):
    products = Product.objects.filter(available=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)
'''

class ProductViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows users to be viewed or edited.
    '''
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


# Simple views for static pages
class AboutView(TemplateView):
    template_name = 'oscar/pages/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'About Us'
        return context


class ContactView(TemplateView):
    template_name = 'oscar/pages/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contact Us'
        return context


def search_products(request):
    from apps.search.product_filters import filter_context

    query = request.GET.get('q', '').strip()

    context = {
        'search_query': query,
        'page_title': f'Search results for "{query}"',
    }

    if query:
        # Relevance-ranked, multi-word search (title/description/UPC/category),
        # then the shared price/vendor/category/stock filters + pagination.
        # preserve_order keeps relevance ranking unless the shopper picks a sort.
        from apps.search.product_filters import build_search_queryset

        results = build_search_queryset(query)
        context.update(filter_context(request, results, preserve_order=True))
    else:
        context['total_count'] = 0

    return render(request, 'oscar/search/search.html', context)
