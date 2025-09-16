from django.urls import path
from ..dashboard import views

app_name = "kitchen"

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu_items, name="menu_items"),
    path("menu/add/", views.add_menu_item, name="add_menu_item"),
    path("orders/", views.order_list, name="order_list"),
]
