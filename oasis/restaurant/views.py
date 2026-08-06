from rest_framework import viewsets, permissions
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.views import generic

from .models import Restaurant, Category, Order
from .serializers import RestaurantSerializer, OrderSerializer


# ---------------------------------------------------------------------------
# API (unchanged) — customers browse restaurants & manage their own orders
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Storefront (HTML) — real data from the database
# ---------------------------------------------------------------------------
class RestaurantListView(generic.ListView):
    """Public directory of active restaurants."""
    template_name = "restaurant/restaurant_list.html"
    context_object_name = "restaurants"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Restaurant.objects.filter(is_active=True)
            .annotate(
                num_items=Count(
                    "categories__items",
                    filter=Q(categories__items__is_available=True),
                    distinct=True,
                )
            )
            .order_by("name")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class RestaurantDetailView(generic.DetailView):
    """A single restaurant with its menu grouped by category."""
    model = Restaurant
    template_name = "restaurant/restaurant_detail.html"
    context_object_name = "restaurant"

    def get_queryset(self):
        return Restaurant.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only show categories that have at least one available item.
        categories = (
            self.object.categories.prefetch_related("items__addons")
            .order_by("name")
        )
        menu = []
        for category in categories:
            items = [i for i in category.items.all() if i.is_available]
            if items:
                menu.append({"category": category, "items": items})
        context["menu"] = menu
        return context
