from django import template
from django.db.models import Q, Sum

register = template.Library()


@register.simple_tag
def seller_earnings(user):
    """
    Return earnings totals for the vendor(s) the user belongs to::

        {total, pending, paid, orders}

    ``total`` is lifetime net earnings, ``pending`` is what's not yet paid out.
    """
    from vendor.models import VendorSale

    empty = {"total": 0, "pending": 0, "paid": 0, "orders": 0}
    if not user.is_authenticated:
        return empty

    partner_ids = list(user.partners.values_list("id", flat=True))
    if not partner_ids:
        return empty

    qs = VendorSale.objects.filter(partner_id__in=partner_ids)
    agg = qs.aggregate(
        total=Sum("net"),
        pending=Sum("net", filter=Q(status=VendorSale.PENDING)),
        paid=Sum("net", filter=Q(status=VendorSale.PAID)),
    )
    return {
        "total": agg["total"] or 0,
        "pending": agg["pending"] or 0,
        "paid": agg["paid"] or 0,
        "orders": qs.values("order").distinct().count(),
    }


@register.simple_tag
def seller_rating(partner):
    """
    Aggregate seller feedback for a partner::

        {avg, count, positive_pct}

    ``avg`` is the mean 1-5 score, ``positive_pct`` the share of ratings >= 4
    (Amazon's "positive feedback" metric). Returns count 0 when unrated.
    """
    from django.db.models import Avg, Count

    empty = {"avg": None, "count": 0, "positive_pct": 0}
    if partner is None:
        return empty

    from vendor.models import SellerFeedback

    qs = SellerFeedback.objects.filter(partner=partner)
    agg = qs.aggregate(avg=Avg("score"), count=Count("id"))
    count = agg["count"] or 0
    if not count:
        return empty
    positive = qs.filter(score__gte=4).count()
    return {
        "avg": round(agg["avg"], 1),
        "count": count,
        "positive_pct": round(100 * positive / count),
    }


@register.simple_tag
def sellers_for_order(order):
    """Distinct partners (sellers) that supplied lines in this order."""
    from oscar.core.loading import get_model

    Partner = get_model("partner", "Partner")
    partner_ids = order.lines.values_list("partner_id", flat=True)
    return Partner.objects.filter(id__in=[p for p in partner_ids if p]).distinct()


@register.simple_tag
def seller_feedback_given(user, order, partner):
    """True if the user has already left feedback for this seller on this order."""
    if not user.is_authenticated:
        return False
    from vendor.models import SellerFeedback

    return SellerFeedback.objects.filter(user=user, order=order, partner=partner).exists()


@register.simple_tag
def seller_for_product(product):
    """
    Return the vendor (Oscar ``Partner``) that sells the given product, or
    ``None``. The seller is taken from the product's first stock record; for
    parent products we fall back to the first child that has one.
    """
    if product is None:
        return None

    stockrecord = product.stockrecords.first()
    if stockrecord is not None:
        return stockrecord.partner

    if product.is_parent:
        for child in product.get_public_children():
            stockrecord = child.stockrecords.first()
            if stockrecord is not None:
                return stockrecord.partner

    return None
