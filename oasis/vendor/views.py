from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, TemplateView

from oscar.core.loading import get_model

from .forms import (
    BecomeSellerForm,
    PayoutSettingsForm,
    ShopSettingsForm,
    VendorProfileForm,
)
from .utils import get_or_create_profile, make_user_a_seller

Partner = get_model("partner", "Partner")
Product = get_model("catalogue", "Product")


def _user_is_seller(user):
    return user.is_authenticated and user.partners.exists()


class BecomeSellerView(LoginRequiredMixin, FormView):
    """
    Instant, self-service vendor onboarding.

    A logged-in customer submits a shop name and is immediately turned into a
    marketplace vendor (a Partner is created, they're linked to it, and they're
    granted dashboard access), then redirected to their new dashboard.
    """

    template_name = "oscar/vendor/become_seller.html"
    form_class = BecomeSellerForm
    success_url = reverse_lazy("dashboard:index")

    def dispatch(self, request, *args, **kwargs):
        # Already a vendor? Skip the form and go straight to the dashboard.
        if request.user.is_authenticated and request.user.partners.exists():
            return redirect("dashboard:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            make_user_a_seller(self.request.user, form.cleaned_data["shop_name"])
        messages.success(
            self.request,
            "Your shop is live! You can now add products and manage orders "
            "from your seller dashboard.",
        )
        return super().form_valid(form)


class ShopSettingsView(LoginRequiredMixin, TemplateView):
    """
    Lets a vendor edit their own shop: the Partner name plus their storefront
    branding (tagline, description, logo, banner). Non-vendors are redirected
    to the onboarding page.
    """

    template_name = "oscar/vendor/shop_settings.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.partners.exists():
            return redirect("vendor:become-seller")
        return super().dispatch(request, *args, **kwargs)

    def get_forms(self, data=None, files=None):
        partner = self.request.user.partners.first()
        profile = get_or_create_profile(partner)
        return (
            ShopSettingsForm(data=data, instance=partner),
            VendorProfileForm(data=data, files=files, instance=profile),
            PayoutSettingsForm(data=data, instance=profile),
        )

    def get(self, request, *args, **kwargs):
        shop_form, profile_form, payout_form = self.get_forms()
        return self.render_to_response(
            self.get_context_data(
                shop_form=shop_form, profile_form=profile_form, payout_form=payout_form
            )
        )

    def post(self, request, *args, **kwargs):
        shop_form, profile_form, payout_form = self.get_forms(
            data=request.POST, files=request.FILES
        )
        if shop_form.is_valid() and profile_form.is_valid() and payout_form.is_valid():
            shop_form.save()
            profile_form.save()
            payout_form.save()
            messages.success(request, "Your shop settings have been saved.")
            return redirect("vendor:shop-settings")
        return self.render_to_response(
            self.get_context_data(
                shop_form=shop_form, profile_form=profile_form, payout_form=payout_form
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.request.user.partners.first()
        return ctx


class VendorStoreView(ListView):
    """
    Public storefront for a single vendor — their own branded shop showing
    all of their products (Amazon-style "seller store").
    """

    template_name = "oscar/vendor/store.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        self.partner = get_object_or_404(Partner, code=self.kwargs["code"])
        return (
            Product.objects.browsable()
            .filter(stockrecords__partner=self.partner)
            .distinct()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["profile"] = getattr(self.partner, "vendor_profile", None)
        ctx["product_count"] = self.get_queryset().count()
        return ctx


class VendorSalesView(LoginRequiredMixin, ListView):
    """
    A seller's "Sales & payouts" page — every VendorSale row for the vendor(s)
    they belong to, with running earnings totals.
    """

    template_name = "oscar/vendor/sales.html"
    context_object_name = "sales"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _user_is_seller(request.user):
            return redirect("vendor:become-seller")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from .models import VendorSale

        return (
            VendorSale.objects.filter(partner__in=self.request.user.partners.all())
            .select_related("order", "partner")
        )

    def get_context_data(self, **kwargs):
        from .templatetags.vendor_tags import seller_earnings

        ctx = super().get_context_data(**kwargs)
        ctx["earnings"] = seller_earnings(self.request.user)
        return ctx


class StoreListView(ListView):
    """A directory of all vendor stores that have at least one product."""

    template_name = "oscar/vendor/store_list.html"
    context_object_name = "partners"
    paginate_by = 24

    def get_queryset(self):
        return (
            Partner.objects.filter(stockrecords__isnull=False)
            .annotate(num_products=Count("stockrecords__product", distinct=True))
            .order_by("name")
        )
