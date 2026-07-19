from django.urls import path

from .views import (
    BecomeSellerView,
    ShopSettingsView,
    StoreListView,
    VendorSalesView,
    VendorStoreView,
)

app_name = "vendor"

urlpatterns = [
    path("sell/", BecomeSellerView.as_view(), name="become-seller"),
    path("settings/", ShopSettingsView.as_view(), name="shop-settings"),
    path("payouts/", VendorSalesView.as_view(), name="sales"),
    path("stores/", StoreListView.as_view(), name="store-list"),
    path("store/<slug:code>/", VendorStoreView.as_view(), name="store"),
]
