from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("thread/<int:pk>/", views.ThreadView.as_view(), name="thread"),
    path("contact/<slug:code>/", views.ContactSellerView.as_view(), name="contact"),
]
