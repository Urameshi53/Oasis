from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from .forms import BecomeRiderForm
from .models import Delivery, RiderProfile


def _rider_profile(user):
    return getattr(user, "rider_profile", None)


class RiderRequiredMixin(LoginRequiredMixin):
    """Ensure the user is a rider; otherwise send them to onboarding."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and _rider_profile(request.user) is None:
            return redirect("rider:become-rider")
        return super().dispatch(request, *args, **kwargs)


class BecomeRiderView(LoginRequiredMixin, CreateView):
    """Instant, self-service rider onboarding."""

    form_class = BecomeRiderForm
    template_name = "oscar/rider/become_rider.html"
    success_url = reverse_lazy("rider:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and _rider_profile(request.user) is not None:
            return redirect("rider:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request,
            "You're now a rider! Claim a delivery below to start earning.",
        )
        return super().form_valid(form)


class RiderDashboardView(RiderRequiredMixin, TemplateView):
    template_name = "oscar/rider/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = _rider_profile(self.request.user)
        mine = Delivery.objects.filter(rider=profile).select_related(
            "order", "order__shipping_address"
        )
        available = Delivery.objects.none()
        if profile.is_available:
            available = Delivery.objects.filter(
                status=Delivery.PENDING, rider__isnull=True
            ).select_related("order", "order__shipping_address")

        ctx.update(
            profile=profile,
            available=available,
            active=mine.filter(status__in=[Delivery.CLAIMED, Delivery.PICKED_UP]),
            history=mine.filter(status=Delivery.DELIVERED),
            delivered_count=mine.filter(status=Delivery.DELIVERED).count(),
        )
        return ctx


class ClaimDeliveryView(RiderRequiredMixin, View):
    def post(self, request, pk):
        profile = _rider_profile(request.user)
        with transaction.atomic():
            delivery = get_object_or_404(
                Delivery.objects.select_for_update(), pk=pk
            )
            if delivery.is_available:
                delivery.claim(profile)
                messages.success(request, f"You claimed order {delivery.order.number}.")
            else:
                messages.error(request, "Sorry, that delivery was already taken.")
        return redirect("rider:dashboard")


class UpdateDeliveryView(RiderRequiredMixin, View):
    def post(self, request, pk):
        profile = _rider_profile(request.user)
        delivery = get_object_or_404(Delivery, pk=pk, rider=profile)
        action = request.POST.get("action")
        if action == "pick_up" and delivery.status == Delivery.CLAIMED:
            delivery.mark_picked_up()
            messages.success(request, f"Order {delivery.order.number} picked up.")
        elif action == "deliver" and delivery.status == Delivery.PICKED_UP:
            delivery.mark_delivered()
            messages.success(request, f"Order {delivery.order.number} delivered. Nice work!")
        else:
            messages.error(request, "That update isn't valid for this delivery.")
        return redirect("rider:dashboard")


class ToggleAvailabilityView(RiderRequiredMixin, View):
    def post(self, request):
        profile = _rider_profile(request.user)
        profile.is_available = not profile.is_available
        profile.save(update_fields=["is_available"])
        messages.info(
            request,
            "You're now online." if profile.is_available else "You're now offline.",
        )
        return redirect("rider:dashboard")
