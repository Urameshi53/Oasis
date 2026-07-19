from django import template
from django.db.models import Q, Sum

register = template.Library()


@register.simple_tag
def rider_earnings(user):
    """
    Earnings for a rider::

        {total, pending, paid, deliveries}

    ``total`` is fees for all completed (delivered) jobs; ``pending`` is what's
    not yet paid out.
    """
    from rider.models import Delivery, RiderProfile

    empty = {"total": 0, "pending": 0, "paid": 0, "deliveries": 0}
    profile = getattr(user, "rider_profile", None) if user.is_authenticated else None
    if profile is None:
        return empty

    done = Delivery.objects.filter(rider=profile, status=Delivery.DELIVERED)
    agg = done.aggregate(
        total=Sum("fee"),
        pending=Sum("fee", filter=Q(payout_status=Delivery.PAYOUT_PENDING)),
        paid=Sum("fee", filter=Q(payout_status=Delivery.PAYOUT_PAID)),
    )
    return {
        "total": agg["total"] or 0,
        "pending": agg["pending"] or 0,
        "paid": agg["paid"] or 0,
        "deliveries": done.count(),
    }
