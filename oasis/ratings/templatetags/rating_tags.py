"""
Amazon-style rating helpers built on Oscar's reviews (see [[oasis-*]] memory).

- ``{% star_icons value %}``      -> row of filled/half/empty Bootstrap-Icon stars
- ``{% rating_breakdown product %}`` -> [{score, count, pct}, ...] 5..1 for a histogram
- ``{% is_verified_purchase review %}`` -> did the reviewer actually buy the product?
"""

from django import template
from django.utils.safestring import mark_safe

from oscar.core.loading import get_model

register = template.Library()

Line = get_model("order", "Line")


@register.simple_tag
def star_icons(value, out_of=5):
    """Render ``value`` (0..out_of) as filled / half / empty star icons."""
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0

    icons = []
    for i in range(1, out_of + 1):
        if value >= i:
            icons.append('<i class="bi bi-star-fill"></i>')
        elif value >= i - 0.5:
            icons.append('<i class="bi bi-star-half"></i>')
        else:
            icons.append('<i class="bi bi-star"></i>')
    return mark_safe('<span class="stars" aria-hidden="true">%s</span>' % "".join(icons))


@register.simple_tag
def rating_breakdown(product):
    """
    Distribution of approved review scores for ``product`` as a list of
    ``{score, count, pct}`` dicts, 5 stars down to 1, for a histogram.
    """
    reviews = product.reviews.approved()
    total = reviews.count()
    counts = {s: 0 for s in range(1, 6)}
    for score in reviews.values_list("score", flat=True):
        rounded = max(1, min(5, int(round(score or 0))))
        counts[rounded] += 1

    rows = []
    for score in range(5, 0, -1):
        c = counts[score]
        rows.append(
            {
                "score": score,
                "count": c,
                "pct": round(100 * c / total) if total else 0,
            }
        )
    return rows


@register.simple_tag
def is_verified_purchase(review):
    """True if the review's author has an order line for the reviewed product."""
    user_id = getattr(review, "user_id", None)
    if not user_id:
        return False
    return Line.objects.filter(
        order__user_id=user_id, product_id=review.product_id
    ).exists()
