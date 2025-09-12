from django.urls import path
from . import dashboard_views

app_name = "restaurant"

urlpatterns = [
    path("", dashboard_views.dashboard_home, name="dashboard_home"),
    path("menu/", dashboard_views.menu_items, name="menu_items"),
    path("menu/add/", dashboard_views.add_menu_item, name="add_menu_item"),
    path("orders/", dashboard_views.order_list, name="order_list"),
]
