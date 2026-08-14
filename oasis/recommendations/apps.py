from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    """
    Lightweight, model-less app that surfaces product recommendations
    ("recently viewed", "products like this") from Oscar's analytics data.
    """

    name = "recommendations"
    verbose_name = "Recommendations"
