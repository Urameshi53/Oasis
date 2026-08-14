from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .models import Membership


def _price():
    return Decimal(str(getattr(settings, "MEMBERSHIP_PRICE", 15)))


def _discount_percent():
    return getattr(settings, "MEMBERSHIP_DISCOUNT_PERCENT", 5)


class MembershipView(LoginRequiredMixin, TemplateView):
    """Landing + manage page for Oasis Plus."""

    template_name = "oscar/membership/membership.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["membership"] = Membership.objects.filter(user=self.request.user).first()
        ctx["price"] = _price()
        ctx["discount_percent"] = _discount_percent()
        return ctx


class JoinView(LoginRequiredMixin, View):
    """Activate (or renew) a 30-day membership. No real billing in dev."""

    def post(self, request, *args, **kwargs):
        membership, created = Membership.objects.get_or_create(
            user=request.user,
            defaults={
                "expires_at": timezone.now(),
                "price": _price(),
            },
        )
        membership.price = _price()
        membership.renew(30)
        messages.success(
            request, "Welcome to Oasis Plus! Your member discount is now active."
        )
        return redirect("membership:home")


class CancelView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        membership = Membership.objects.filter(user=request.user).first()
        if membership:
            membership.is_active = False
            membership.save(update_fields=["is_active"])
            messages.info(request, "Your Oasis Plus membership has been cancelled.")
        return redirect("membership:home")
