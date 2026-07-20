from django.urls import path

from .views import CustomerAnalyticsView

app_name = "insights"

urlpatterns = [
    path("", CustomerAnalyticsView.as_view(), name="customer-analytics"),
]
