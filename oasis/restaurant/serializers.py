from rest_framework import serializers
from .models import Restaurant, Category, MenuItem, Addon, Order, OrderItem


class AddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addon
        fields = ["id", "name", "price"]


class MenuItemSerializer(serializers.ModelSerializer):
    addons = AddonSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "name", "description", "base_price", "image", "is_available", "addons"]


class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "items"]


class RestaurantSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = ["id", "name", "description", "logo", "phone", "address", "categories"]


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant = RestaurantSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "restaurant", "status", "total_price", "delivery_address", "items", "created_at"]
