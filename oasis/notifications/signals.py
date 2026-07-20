"""Fire notifications from order events."""

import logging

from django.dispatch import receiver
from django.urls import NoReverseMatch, reverse

from oscar.apps.order.signals import order_placed

from .models import Notification
from .utils import notify, notify_many

logger = logging.getLogger("notifications")


def _safe_reverse(name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        return ""


@receiver(order_placed, dispatch_uid="notifications.on_order_placed")
def on_order_placed(sender, order=None, **kwargs):
    if order is None:
        return
    try:
        _notify_order_placed(order)
    except Exception:
        logger.exception("Failed to send order notifications for %s", order.number)


def _notify_order_placed(order):
    # 1) Customer
    if order.user_id:
        notify(
            order.user,
            f"Your order {order.number} has been placed 🎉",
            url=_safe_reverse("customer:order", order_number=order.number),
            icon="bag-check",
            level=Notification.SUCCESS,
        )

    # 2) Store owners whose products are in the order
    partners = {line.partner for line in order.lines.all() if line.partner_id}
    dashboard_url = _safe_reverse("dashboard:order-detail", number=order.number)
    for partner in partners:
        notify_many(
            list(partner.users.all()),
            f"New order {order.number} includes your products.",
            url=dashboard_url,
            icon="shop",
            level=Notification.SUCCESS,
        )

    # 3) Available riders — a new delivery is up for grabs
    from django.contrib.auth import get_user_model

    User = get_user_model()
    rider_users = User.objects.filter(rider_profile__is_available=True)
    notify_many(
        list(rider_users),
        f"New delivery available to claim ({order.number}).",
        url=_safe_reverse("rider:dashboard"),
        icon="scooter",
        level=Notification.INFO,
    )
