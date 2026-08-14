"""
Template tags that surface product recommendations from Oscar's analytics data.

No models of our own — we read the ``analytics`` app's ``UserProductView``
(per-user browsing history, populated by the ``product_viewed`` signal) and
``ProductRecord`` (aggregate popularity) records. See [[oasis-admin-analytics]].
"""

from django import template

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
UserProductView = get_model("analytics", "UserProductView")
Line = get_model("order", "Line")

register = template.Library()


@register.simple_tag
def best_sellers(limit=8, exclude=None):
    """
    Most-purchased browsable products, from the analytics ``ProductRecord``
    (``stats`` relation), popularity descending. Falls back gracefully when
    nothing has sold yet (returns []).
    """
    qs = (
        Product.objects.browsable()
        .filter(stats__num_purchases__gt=0)
        .order_by("-stats__num_purchases", "-stats__num_views")
    )
    exclude_id = getattr(exclude, "id", None)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return list(qs.distinct()[:limit])


@register.simple_tag
def buy_again(request, limit=8):
    """
    Distinct browsable products the current user has bought before, most
    recently purchased first. Empty for anonymous users or those with no orders.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return []

    rows = (
        Line.objects.filter(order__user=user, product__isnull=False)
        .order_by("-order__date_placed")
        .values_list("product_id", flat=True)
    )
    ordered_ids = []
    seen = set()
    for pid in rows:
        if pid in seen:
            continue
        seen.add(pid)
        ordered_ids.append(pid)
        if len(ordered_ids) >= limit:
            break

    if not ordered_ids:
        return []
    products = Product.objects.browsable().in_bulk(ordered_ids)
    return [products[pid] for pid in ordered_ids if pid in products]


@register.simple_tag
def recently_viewed_products(request, exclude=None, limit=6):
    """
    Return the current user's most recently viewed browsable products,
    newest first, optionally excluding one product (e.g. the one on screen).

    Returns an empty list for anonymous users. Because the whole site is
    behind a login wall this is per-user and cross-device (unlike Oscar's
    cookie-based history).
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return []

    exclude_id = getattr(exclude, "id", None)

    # Most-recent view per product: walk views newest-first, keep first sighting.
    views = (
        UserProductView.objects.filter(user=user)
        .order_by("-date_created")
        .values_list("product_id", flat=True)
    )
    ordered_ids = []
    seen = set()
    for pid in views:
        if pid == exclude_id or pid in seen:
            continue
        seen.add(pid)
        ordered_ids.append(pid)
        if len(ordered_ids) >= limit:
            break

    if not ordered_ids:
        return []

    products = Product.objects.browsable().in_bulk(ordered_ids)
    return [products[pid] for pid in ordered_ids if pid in products]


@register.simple_tag
def products_like(product, limit=6):
    """
    Return browsable products similar to ``product`` — same category first,
    ranked by popularity (purchases then views via the related ProductRecord),
    excluding the product itself. Falls back to same product class when the
    product has no categories.
    """
    if product is None:
        return []

    qs = Product.objects.browsable().exclude(id=product.id)

    category_ids = list(product.categories.values_list("id", flat=True))
    if category_ids:
        qs = qs.filter(categories__in=category_ids)
    elif product.product_class_id:
        qs = qs.filter(product_class_id=product.product_class_id)
    else:
        return []

    # Popularity: ProductRecord is a OneToOne (related_name "stats"); order by
    # purchases then views, nulls (never-recorded products) sorting last.
    qs = qs.distinct().order_by(
        "-stats__num_purchases", "-stats__num_views", "-date_created"
    )
    return list(qs[:limit])
