from django.urls import path

from .views import (
    BecomeRiderView,
    ClaimDeliveryView,
    RiderDashboardView,
    ToggleAvailabilityView,
    UpdateDeliveryView,
)

app_name = "rider"

urlpatterns = [
    path("", RiderDashboardView.as_view(), name="dashboard"),
    path("join/", BecomeRiderView.as_view(), name="become-rider"),
    path("availability/", ToggleAvailabilityView.as_view(), name="toggle-availability"),
    path("delivery/<int:pk>/claim/", ClaimDeliveryView.as_view(), name="claim"),
    path("delivery/<int:pk>/update/", UpdateDeliveryView.as_view(), name="update"),
]
