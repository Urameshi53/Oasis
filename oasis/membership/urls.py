from django.urls import path

from . import views

app_name = "membership"

urlpatterns = [
    path("", views.MembershipView.as_view(), name="home"),
    path("join/", views.JoinView.as_view(), name="join"),
    path("cancel/", views.CancelView.as_view(), name="cancel"),
]
