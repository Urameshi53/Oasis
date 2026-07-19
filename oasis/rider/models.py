from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_delivery_fee():
    return Decimal(str(getattr(settings, "RIDER_DELIVERY_FEE", 10)))


class RiderProfile(models.Model):
    """
    A delivery rider. The presence of a RiderProfile marks a user as a rider
    (mirrors how an Oscar ``Partner`` marks a user as a seller).
    """

    VEHICLES = [
        ("motorbike", "Motorbike"),
        ("bicycle", "Bicycle"),
        ("car", "Car"),
        ("foot", "On foot"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rider_profile"
    )
    phone = models.CharField(max_length=30, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLES, default="motorbike")
    #: When off, the rider won't be shown new deliveries to claim.
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rider: {self.user.get_full_name() or self.user.get_username()}"


class Delivery(models.Model):
    """A delivery job for one order, claimable by a rider from a shared pool."""

    PENDING, CLAIMED, PICKED_UP, DELIVERED, CANCELLED = (
        "pending",
        "claimed",
        "picked_up",
        "delivered",
        "cancelled",
    )
    STATUS_CHOICES = [
        (PENDING, "Waiting for a rider"),
        (CLAIMED, "Claimed"),
        (PICKED_UP, "Picked up"),
        (DELIVERED, "Delivered"),
        (CANCELLED, "Cancelled"),
    ]

    PAYOUT_PENDING, PAYOUT_PAID = "pending", "paid"
    PAYOUT_CHOICES = [(PAYOUT_PENDING, "Pending"), (PAYOUT_PAID, "Paid out")]

    order = models.OneToOneField(
        "order.Order", on_delete=models.CASCADE, related_name="delivery"
    )
    rider = models.ForeignKey(
        RiderProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    #: What the rider earns for completing this delivery (set when created).
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=default_delivery_fee)
    payout_status = models.CharField(
        max_length=12, choices=PAYOUT_CHOICES, default=PAYOUT_PENDING
    )
    currency = models.CharField(max_length=12, default="GHS")
    claimed_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "Deliveries"

    def __str__(self):
        return f"Delivery for order {self.order.number} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in (self.CLAIMED, self.PICKED_UP)

    @property
    def is_available(self):
        return self.status == self.PENDING and self.rider_id is None

    # --- lifecycle transitions ---

    def claim(self, rider):
        self.rider = rider
        self.status = self.CLAIMED
        self.claimed_at = timezone.now()
        self.save(update_fields=["rider", "status", "claimed_at"])

    def mark_picked_up(self):
        self.status = self.PICKED_UP
        self.picked_up_at = timezone.now()
        self.save(update_fields=["status", "picked_up_at"])

    def mark_delivered(self):
        self.status = self.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at"])
