"""
URL configuration for oasis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.apps import apps
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from .views import *
from rest_framework.authtoken.views import obtain_auth_token

from oasis.views import paystack_callback

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    path('paystack/callback/', paystack_callback, name='paystack-callback'),

    path('admin/', admin.site.urls),
    path("api/restaurant/", include("restaurant.urls")),
    path('restaurant/', include("restaurant.urls")),
    path("api/catalogue/", include("apps.catalogue.urls")),
    path('api/', include(router.urls)),
    path("api/auth/login/", obtain_auth_token),
    path('api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('payments/', include('payments.urls')),
    
    # Page routes
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),

    path('', include(apps.get_app_config('oscar').urls[0])),
]


if settings.DEBUG:

    # Server statics and uploaded media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    