from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .views import ProductViewSet
from . import views

router = DefaultRouter()
router.register(r'catalogue', ProductViewSet, basename='catalogue')


urlpatterns = [
    path('api/', include(router.urls)),
]
