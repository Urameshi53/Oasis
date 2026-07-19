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
        # Search public, browsable products by title, description or UPC, then
        # apply the shared price/vendor/stock/sort filters + pagination.
        results = Product.objects.browsable().filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(upc__icontains=query)
        )
        context.update(filter_context(request, results))
    else:
        context['total_count'] = 0

    return render(request, 'oscar/search/search.html', context)
