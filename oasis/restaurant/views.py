from rest_framework import viewsets, permissions
from .models import Restaurant, Order
from .serializers import RestaurantSerializer, OrderSerializer


class RestaurantViewSet(viewsets.ReadOnlyModelViewSet):
    """Customers can browse restaurants & menus"""
    queryset = Restaurant.objects.filter(is_active=True)
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    """Customers place orders, restaurants manage them"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()  # Admin sees all
        return Order.objects.filter(customer=user)  # Customers see their own orders

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
