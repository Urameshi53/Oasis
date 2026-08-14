from django.conf import settings


def payout_schedule(request):
    """Expose the next payout run time to sellers/riders (10am next working day)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    from .payouts import next_payout_datetime

    return {"next_payout_at": next_payout_datetime()}


def wishlist(request):
    """
    Expose the set of product IDs in the user's wishlist(s) + a total count,
    so product cards can show a filled/outline heart and the header a badge.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"wishlist_product_ids": set(), "wishlist_count": 0}

    from oscar.core.loading import get_model

    Line = get_model("wishlists", "Line")
    ids = set(
        Line.objects.filter(wishlist__owner=user).values_list("product_id", flat=True)
    )
    return {"wishlist_product_ids": ids, "wishlist_count": len(ids)}


def modern_settings(request):
    return {
        'site_name': getattr(settings, 'OSCAR_SHOP_NAME', 'Modern Store'),
        'site_tagline': getattr(settings, 'OSCAR_SHOP_TAGLINE', 'Premium E-commerce'),
        'current_year': '2024',
        'featured_categories': [
            {'name': 'Electronics', 'icon': 'bi-phone', 'color': 'primary'},
            {'name': 'Fashion', 'icon': 'bi-tshirt', 'color': 'danger'},
            {'name': 'Home & Garden', 'icon': 'bi-house', 'color': 'success'},
            {'name': 'Sports', 'icon': 'bi-trophy', 'color': 'warning'},
            {'name': 'Books', 'icon': 'bi-book', 'color': 'info'},
            {'name': 'Beauty', 'icon': 'bi-flower1', 'color': 'secondary'},
        ]
    }