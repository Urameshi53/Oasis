from rest_framework.decorators import api_view
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

'''
@api_view(["GET"])
def product_list(request):
    products = Product.objects.filter(available=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)'''

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Customers can browse all products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]