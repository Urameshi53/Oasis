"""Create a delivery job whenever an order is placed."""

import logging

from django.dispatch import receiver

from oscar.apps.order.signals import order_placed

logger = logging.getLogger("rider")


@receiver(order_placed, dispatch_uid="rider.create_delivery_for_order")
def create_delivery_for_order(sender, order=None, **kwargs):
    if order is None:
        return
    from .models import Delivery

    try:
        Delivery.objects.get_or_create(
            order=order, defaults={"currency": order.currency}
        )
    except Exception:
        logger.exception("Failed to create delivery for order %s", order.number)
