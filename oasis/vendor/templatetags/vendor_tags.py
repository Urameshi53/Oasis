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
