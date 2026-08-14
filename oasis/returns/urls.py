from django.urls import path

from . import views

app_name = "returns"

urlpatterns = [
    path("", views.ReturnListView.as_view(), name="list"),
    path("seller/", views.SellerReturnListView.as_view(), name="seller-list"),
    path("order/<str:order_number>/new/", views.ReturnCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ReturnDetailView.as_view(), name="detail"),
    path("<int:pk>/action/", views.ReturnActionView.as_view(), name="action"),
    path("<int:pk>/cancel/", views.ReturnCancelView.as_view(), name="cancel"),
]
