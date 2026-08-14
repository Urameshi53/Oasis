"""
Product questions & answers ("Customer Q&A").

Any signed-in shopper can ask a question about a product; other shoppers or the
seller can answer. Answers from the product's seller are flagged so buyers can
trust them. Asking notifies the seller; answering notifies the asker.
"""

from django.conf import settings
from django.db import models


class ProductQuestion(models.Model):
    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, related_name="questions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_questions"
    )
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Q{self.pk}: {self.body[:50]}"

    @property
    def answer_count(self):
        return self.answers.count()


class ProductAnswer(models.Model):
    question = models.ForeignKey(
        ProductQuestion, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_answers"
    )
    body = models.TextField()
    #: True if answered by the product's seller (set at creation).
    is_seller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Seller answers first, then oldest-first.
        ordering = ("-is_seller", "created_at")

    def __str__(self):
        return f"A{self.pk} to Q{self.question_id}"
