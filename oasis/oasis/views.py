# yourapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from oscar.apps.order.models import Order
import requests
from oscar.apps.catalogue.models import Product
from rest_framework import permissions, viewsets
from .serializers import ProductSerializer


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
