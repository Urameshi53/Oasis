"""Signal handlers that keep the vendor sales ledger in sync with orders."""

import logging

from django.dispatch import receiver

from oscar.apps.order.signals import order_placed

from .payments import record_vendor_sales

logger = logging.getLogger("vendor")


@receiver(order_placed, dispatch_uid="vendor.create_vendor_sales_ledger")
def create_vendor_sales_ledger(sender, order=None, **kwargs):
    """When an order is placed, split it into per-vendor ledger rows."""
    if order is None:
        return
    try:
        record_vendor_sales(order)
    except Exception:  # never break order placement over ledger accounting
        logger.exception("Failed to record vendor sales for order %s", order.number)
