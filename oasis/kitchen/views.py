from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Restaurant, MenuItem, Order
from .forms import MenuItemForm

@login_required
def dashboard_home(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    orders = restaurant.orders.all().order_by("-created_at")[:10]  # last 10
    return render(request, "kitchen/index.html", {"restaurant": restaurant, "orders": orders})


@login_required
def menu_items(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    items = restaurant.categories.all().prefetch_related("items")
    return render(request, "restaurant/menu_items.html", {"items": items})


@login_required
def add_menu_item(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save(commit=False)
            menu_item.category.restaurant = restaurant
            menu_item.save()
            return redirect("restaurant:menu_items")
    else:
        form = MenuItemForm()
    return render(request, "restaurant/add_menu_item.html", {"form": form})


@login_required
def order_list(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    orders = restaurant.orders.all().order_by("-created_at")
    return render(request, "restaurant/order_list.html", {"orders": orders})
