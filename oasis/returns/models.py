"""
Returns / refunds (RMA) for the Oscar marketplace.

A customer opens a ``ReturnRequest`` against a delivered order, choosing which
lines and quantities to send back and why. The seller(s) whose products are in
the request (or staff) approve or reject it; on refund we restock and record a
refund payment event. Transitions notify the customer.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from oscar.core.loading import get_model


class ReturnRequest(models.Model):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (REFUNDED, "Refunded"),
        (CANCELLED, "Cancelled"),
    ]
    #: Statuses where nothing more will happen.
    CLOSED_STATUSES = (REJECTED, REFUNDED, CANCELLED)

    REASON_CHOICES = [
        ("defective", "Item is defective or damaged"),
        ("wrong_item", "Wrong item was sent"),
        ("not_as_described", "Not as described"),
        ("no_longer_needed", "No longer needed"),
        ("arrived_late", "Arrived too late"),
        ("other", "Other"),
    ]

    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, related_name="return_requests"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="return_requests",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=REQUESTED)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comment = models.TextField(blank=True)
    #: Seller/staff note when resolving (e.g. rejection reason).
    resolution_note = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=12, default="GHS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Return #{self.pk} for order {self.order.number} ({self.get_status_display()})"

    # --- helpers ---

    @property
    def is_open(self):
        return self.status not in self.CLOSED_STATUSES

    @property
    def total_quantity(self):
        return sum(line.quantity for line in self.lines.all())

    def expected_refund(self):
        return sum((line.refund_amount for line in self.lines.all()), Decimal("0.00"))

    def partners(self):
        """Partners (sellers) whose products are in this return."""
        Partner = get_model("partner", "Partner")
        partner_ids = self.lines.values_list("order_line__partner_id", flat=True)
        return Partner.objects.filter(id__in=[p for p in partner_ids if p])

    def can_be_managed_by(self, user):
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        return self.partners().filter(users=user).exists()

    # --- transitions ---

    def _notify_customer(self, message, icon, level):
        try:
            from notifications.utils import notify
            from django.urls import reverse

            notify(
                self.user,
                message,
                url=reverse("returns:detail", args=[self.pk]),
                icon=icon,
                level=level,
            )
        except Exception:
            pass

    def approve(self, note=""):
        self.status = self.APPROVED
        self.resolution_note = note
        self.save(update_fields=["status", "resolution_note", "updated_at"])
        self._notify_customer(
            "Your return for order %s was approved." % self.order.number,
            "bi-check-circle",
            "success",
        )

    def reject(self, note=""):
        self.status = self.REJECTED
        self.resolution_note = note
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolution_note", "resolved_at", "updated_at"])
        self._notify_customer(
            "Your return for order %s was declined." % self.order.number,
            "bi-x-circle",
            "warning",
        )

    def mark_refunded(self, restock=True):
        """Record the refund, optionally restock, and close the request."""
        amount = self.expected_refund()
        self.refund_amount = amount
        self.status = self.REFUNDED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "refund_amount", "resolved_at", "updated_at"])

        if restock:
            for line in self.lines.select_related("order_line__stockrecord"):
                sr = line.order_line.stockrecord
                if sr is not None and sr.num_in_stock is not None:
                    sr.num_in_stock = (sr.num_in_stock or 0) + line.quantity
                    sr.save(update_fields=["num_in_stock"])

        # Record a refund payment event on the order (no external gateway call).
        try:
            source = self.order.sources.first()
            if source is not None:
                source.refund(amount, reference="RETURN-%s" % self.pk)
        except Exception:
            pass

        self._notify_customer(
            "You've been refunded %s %s for order %s."
            % (self.currency, amount, self.order.number),
            "bi-cash-coin",
            "success",
        )


class ReturnLine(models.Model):
    return_request = models.ForeignKey(
        ReturnRequest, on_delete=models.CASCADE, related_name="lines"
    )
    order_line = models.ForeignKey(
        "order.Line", on_delete=models.PROTECT, related_name="return_lines"
    )
    quantity = models.PositiveIntegerField(default=1)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.quantity} x {self.order_line.title}"

    def save(self, *args, **kwargs):
        # Refund = unit price incl tax * quantity, unless explicitly set.
        if not self.refund_amount:
            unit = self.order_line.unit_price_incl_tax or Decimal("0.00")
            self.refund_amount = unit * self.quantity
        super().save(*args, **kwargs)
