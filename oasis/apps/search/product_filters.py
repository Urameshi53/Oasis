"""
Shared product filtering/sorting/pagination for the storefront listing pages
(catalogue, category, search). Kept view-agnostic: pass in a base Product
queryset and the request, get back a ready-to-render context.
"""

from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Min, Q, Value, When

from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")

PER_PAGE = 12


def build_search_queryset(query):
    """
    Relevance-ranked product search over browsable products.

    - Splits the query into terms and requires *every* term to match somewhere
      (title / description / UPC / category) — precise multi-word search.
    - If that returns nothing, falls back to matching *any* term, so a single
      mistyped word still yields results.
    - Ranks results: exact title > title starts-with > title contains > the
      rest (matched only on description/category). Ties break on newest.

    Returns a queryset already ordered by relevance; callers can override the
    order with an explicit ``sort`` via ``filter_context(preserve_order=True)``.
    """
    terms = [t for t in query.split() if t]
    base = Product.objects.browsable()

    def term_q(term):
        return (
            Q(title__icontains=term)
            | Q(description__icontains=term)
            | Q(upc__icontains=term)
            | Q(categories__name__icontains=term)
        )

    and_q = Q()
    for t in terms:
        and_q &= term_q(t)
    qs = base.filter(and_q).distinct() if terms else base.none()

    if terms and not qs.exists():
        or_q = Q()
        for t in terms:
            or_q |= term_q(t)
        qs = base.filter(or_q).distinct()

    # Relevance signals (ordered by priority in the order_by below).
    qs = qs.annotate(
        _m_exact=Case(When(title__iexact=query, then=Value(1)), default=Value(0), output_field=IntegerField()),
        _m_start=Case(When(title__istartswith=query, then=Value(1)), default=Value(0), output_field=IntegerField()),
        _m_title=Case(When(title__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()),
    ).order_by("-_m_exact", "-_m_start", "-_m_title", "-date_created")
    return qs

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


def apply_product_filters(request, queryset, preserve_order=False):
    """
    Apply price/vendor/stock/category filters and sorting from the GET params.

    ``preserve_order``: when True and the shopper hasn't picked an explicit
    sort, keep the incoming queryset's order (used by search to keep relevance).
    """
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

    category = get("category")
    if category:
        cat = Category.objects.filter(slug=category).first()
        if cat is not None:
            # Include the category and all of its descendants.
            ids = [cat.id] + list(cat.get_descendants().values_list("id", flat=True))
            qs = qs.filter(categories__in=ids)

    if get("in_stock"):
        qs = qs.filter(stockrecords__num_in_stock__gt=0)

    sort = get("sort")
    if sort in _SORT_MAP:
        qs = qs.order_by(_SORT_MAP[sort][0])
    elif preserve_order:
        pass  # keep the incoming (e.g. relevance) ordering
    else:
        # Stable default ordering (newest first) so pagination is consistent.
        qs = qs.order_by("-date_created")

    return qs.distinct()


def filter_context(request, base_queryset, per_page=PER_PAGE, preserve_order=False):
    """
    Return a context dict with the filtered, paginated products plus everything
    the filter UI needs (current values, vendor list, sort options, querystring).
    """
    filtered = apply_product_filters(request, base_queryset, preserve_order=preserve_order)

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
        # Categories present in this result set, for a category facet.
        "filter_categories": Category.objects.filter(
            id__in=base_queryset.values_list("categories__id", flat=True)
        )
        .distinct()
        .order_by("name"),
        "sort_options": [(value, label) for value, (_f, label) in SORT_OPTIONS],
        "current": {
            "sort": get("sort", ""),
            "min_price": get("min_price", ""),
            "max_price": get("max_price", ""),
            "vendor": get("vendor", ""),
            "category": get("category", ""),
            "in_stock": bool(get("in_stock")),
        },
        "has_active_filters": any(
            get(k) for k in ("sort", "min_price", "max_price", "vendor", "category", "in_stock")
        ),
    }
