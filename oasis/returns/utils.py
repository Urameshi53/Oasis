"""Return eligibility helpers, shared by views and template tags."""

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone


def return_window_days():
    return getattr(settings, "RETURN_WINDOW_DAYS", 30)


def already_returned_qty(order_line):
    """Quantity of this line tied up in non-rejected return requests."""
    from returns.models import ReturnLine, ReturnRequest

    agg = (
        ReturnLine.objects.filter(order_line=order_line)
        .exclude(return_request__status=ReturnRequest.REJECTED)
        .aggregate(n=Sum("quantity"))
    )
    return agg["n"] or 0


def returnable_qty(order_line):
    """How many units of this line can still be returned."""
    return max(0, order_line.quantity - already_returned_qty(order_line))


def returnable_lines(order):
    """Order lines that still have quantity available to return."""
    return [line for line in order.lines.all() if returnable_qty(line) > 0]


def within_return_window(order):
    days = return_window_days()
    return order.date_placed >= timezone.now() - timezone.timedelta(days=days)


def can_return_order(user, order):
    """True if `user` may open a return against `order`."""
    if not user.is_authenticated or order.user_id != user.id:
        return False
    if not within_return_window(order):
        return False
    return bool(returnable_lines(order))
