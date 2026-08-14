from django.contrib import messages as flash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from oscar.core.loading import get_model

from .models import ProductAnswer, ProductQuestion

Product = get_model("catalogue", "Product")


def _seller_for_product(product):
    from vendor.templatetags.vendor_tags import seller_for_product

    return seller_for_product(product)


def _notify(user, message, url, icon):
    try:
        from notifications.utils import notify

        notify(user, message, url=url, icon=icon, level="info")
    except Exception:
        pass


class AskQuestionView(LoginRequiredMixin, View):
    def post(self, request, product_pk):
        product = get_object_or_404(Product, pk=product_pk)
        body = request.POST.get("body", "").strip()
        if body:
            ProductQuestion.objects.create(product=product, user=request.user, body=body)
            seller = _seller_for_product(product)
            if seller:
                url = product.get_absolute_url() + "#qa"
                for u in seller.users.all():
                    _notify(u, "New question on %s" % product.get_title(), url, "bi-patch-question")
            flash.success(request, "Your question was posted.")
        return redirect(product.get_absolute_url() + "#qa")


class AnswerQuestionView(LoginRequiredMixin, View):
    def post(self, request, question_pk):
        question = get_object_or_404(ProductQuestion, pk=question_pk)
        body = request.POST.get("body", "").strip()
        if body:
            seller = _seller_for_product(question.product)
            is_seller = bool(seller and seller.users.filter(pk=request.user.pk).exists())
            ProductAnswer.objects.create(
                question=question, user=request.user, body=body, is_seller=is_seller
            )
            url = question.product.get_absolute_url() + "#qa"
            if question.user_id != request.user.id:
                _notify(question.user, "Your question got an answer", url, "bi-chat-left-text")
            flash.success(request, "Your answer was posted.")
        return redirect(question.product.get_absolute_url() + "#qa")


class ProductQAListView(ListView):
    """All questions for a product."""

    template_name = "oscar/qa/question_list.html"
    context_object_name = "questions"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.product.questions.prefetch_related("answers", "answers__user", "user")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        return ctx
