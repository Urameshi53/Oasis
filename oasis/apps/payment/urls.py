# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_payment, name='start-payment'),
    path('verify/', views.verify_payment, name='verify-payment'),
]
