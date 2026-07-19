"""
Shared product filtering/sorting/pagination for the storefront listing pages
(catalogue, category, search). Kept view-agnostic: pass in a base Product
queryset and the request, get back a ready-to-render context.
"""

from django.core.paginator import Paginator
from django.db.models import Min

from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")

PER_PAGE = 12

# value -> (order_by field, label)
SORT_OPTIONS = [
    ("newest", ("-date_created", "Newest")),
    ("price-asc", ("_price", "Price: Low to High")),
    ("price-desc", ("-_price", "Price: High to Low")),
    ("name", ("title", "Name: A–Z")),
]
_SORT_MAP = dict(SORT_OPTIONS)


def _to_decimal(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def apply_product_filters(request, queryset):
    """Apply price/vendor/stock filters and sorting from the request GET params."""
    qs = queryset.annotate(_price=Min("stockrecords__price"))
    get = request.GET.get

    min_price = _to_decimal(get("min_price"))
    if min_price is not None:
        qs = qs.filter(_price__gte=min_price)

    max_price = _to_decimal(get("max_price"))
    if max_price is not None:
        qs = qs.filter(_price__lte=max_price)

    vendor = get("vendor")
    if vendor:
        qs = qs.filter(stockrecords__partner__code=vendor)

    if get("in_stock"):
        qs = qs.filter(stockrecords__num_in_stock__gt=0)

    sort = get("sort")
    if sort in _SORT_MAP:
        qs = qs.order_by(_SORT_MAP[sort][0])
    else:
        # Stable default ordering (newest first) so pagination is consistent.
        qs = qs.order_by("-date_created")

    return qs.distinct()


def filter_context(request, base_queryset, per_page=PER_PAGE):
    """
    Return a context dict with the filtered, paginated products plus everything
    the filter UI needs (current values, vendor list, sort options, querystring).
    """
    filtered = apply_product_filters(request, base_queryset)

    paginator = Paginator(filtered, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Querystring without `page`, so pagination links keep the active filters.
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    get = request.GET.get
    return {
        "products": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "total_count": paginator.count,
        "filter_querystring": querystring,
        # Only vendors with products in THIS listing's scope, so the Store
        # dropdown never offers a shop that would return zero results.
        "filter_vendors": Partner.objects.filter(
            stockrecords__product__in=base_queryset
        )
        .distinct()
        .order_by("name"),
        "sort_options": [(value, label) for value, (_f, label) in SORT_OPTIONS],
        "current": {
            "sort": get("sort", ""),
            "min_price": get("min_price", ""),
            "max_price": get("max_price", ""),
            "vendor": get("vendor", ""),
            "in_stock": bool(get("in_stock")),
        },
        "has_active_filters": any(
            get(k) for k in ("sort", "min_price", "max_price", "vendor", "in_stock")
        ),
    }
