from django.urls import path

from . import views

app_name = "qa"

urlpatterns = [
    path("ask/<int:product_pk>/", views.AskQuestionView.as_view(), name="ask"),
    path("answer/<int:question_pk>/", views.AnswerQuestionView.as_view(), name="answer"),
    path("product/<int:product_pk>/", views.ProductQAListView.as_view(), name="list"),
]
