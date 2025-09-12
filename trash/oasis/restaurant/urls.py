from django.urls import path 
from django.conf import settings
from django.conf.urls.static import static

from . import views 

app_name = "oasis"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    #path("keys/", views.KeyDetailView.as_view(), name='keys'),
    #path("<int:user_id>/buy_key/", views.buy_key , name="buy_key"),
    #path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    #path("<int:discussion_id>/post_comment/", views.post_comment , name="post_comment"),
    #path("", views.SearchView.as_view(), name="search"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
