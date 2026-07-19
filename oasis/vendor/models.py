from decimal import Decimal

from django.conf import settings
from django.db import models


class VendorProfile(models.Model):
    """
    Storefront branding + payout config for a marketplace vendor.

    A vendor *is* an Oscar ``Partner`` (see ``vendor.utils.make_user_a_seller``).
    This model hangs optional store-branding and payout details off that Partner
    so each seller can have their own Amazon-style storefront and get paid.
    """

    partner = models.OneToOneField(
        "partner.Partner",
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="vendors/logos/", blank=True, null=True)
    banner = models.ImageField(upload_to="vendors/banners/", blank=True, null=True)

    # --- Payout / settlement ---
    #: Per-vendor commission override (percent). Blank => use the platform default.
    commission_rate = models.DecimalField(
        "Commission rate (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Platform commission on this vendor's sales. Leave blank for the default.",
    )
    #: Paystack subaccount that receives this vendor's share of split payments.
    paystack_subaccount_code = models.CharField(max_length=100, blank=True)
    settlement_bank = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Store profile for {self.partner.display_name}"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("vendor:store", kwargs={"code": self.partner.code})

    @property
    def effective_commission_rate(self):
        """Commission rate (as a percentage Decimal) applied to this vendor."""
        if self.commission_rate is not None:
            return self.commission_rate
        return Decimal(str(getattr(settings, "PLATFORM_COMMISSION_RATE", 10)))


class VendorSale(models.Model):
    """
    Ledger row recording one vendor's share of a single order.

    Created when an order is placed (one row per partner in the order). It is
    the source of truth for what each seller earned and whether they've been
    paid out — independent of how funds were actually routed at the gateway.
    """

    PENDING, PAID, CANCELLED = "pending", "paid", "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PAID, "Paid out"),
        (CANCELLED, "Cancelled"),
    ]

    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, related_name="vendor_sales"
    )
    partner = models.ForeignKey(
        "partner.Partner", on_delete=models.CASCADE, related_name="vendor_sales"
    )
    #: Total the customer paid for this vendor's items in the order.
    gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    #: Platform commission taken from ``gross``.
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    #: What the vendor is owed (``gross - commission``).
    net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="GHS")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("order", "partner")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.partner.display_name}: {self.net} {self.currency} from order {self.order.number}"
