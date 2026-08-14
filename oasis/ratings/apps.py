from django.apps import AppConfig


class RatingsConfig(AppConfig):
    """
    Model-less app providing Amazon-style rating UI helpers (star rendering,
    score histogram, verified-purchase detection) on top of Oscar's reviews.
    """

    name = "ratings"
    verbose_name = "Ratings"
