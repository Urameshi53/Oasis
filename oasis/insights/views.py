"""Admin-only customer behaviour analytics.

Reads Oscar's built-in analytics records (product views, basket additions,
purchases, searches) plus order data. Staff/superusers only — sellers, riders
and customers get a 403.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from oscar.core.loading import get_model

ProductRecord = get_model("analytics", "ProductRecord")
UserRecord = get_model("analytics", "UserRecord")
UserProductView = get_model("analytics", "UserProductView")
UserSearch = get_model("analytics", "UserSearch")
Order = get_model("order", "Order")
User = get_user_model()


def _pct(numerator, denominator):
    return round(numerator / denominator * 100, 1) if denominator else 0


class StaffOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only site admins (staff) may view — everyone else gets 403."""

    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


class CustomerAnalyticsView(StaffOnlyMixin, TemplateView):
    template_name = "oscar/insights/customer_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        last_30 = now - timedelta(days=30)

        orders = Order.objects.all()

        # --- Behaviour funnel (views -> basket -> purchase) ---
        totals = ProductRecord.objects.aggregate(
            views=Sum("num_views"),
            baskets=Sum("num_basket_additions"),
            purchases=Sum("num_purchases"),
        )
        views = totals["views"] or 0
        baskets = totals["baskets"] or 0
        purchases = totals["purchases"] or 0

        # --- Customers ---
        buyers = UserRecord.objects.filter(num_orders__gt=0).count()
        repeat = UserRecord.objects.filter(num_orders__gt=1).count()

        ctx.update(
            # KPIs
            total_customers=User.objects.count(),
            buyers=buyers,
            repeat_customers=repeat,
            repeat_rate=_pct(repeat, buyers),
            new_customers_30d=User.objects.filter(date_joined__gte=last_30).count(),
            total_orders=orders.count(),
            orders_30d=orders.filter(date_placed__gte=last_30).count(),
            total_revenue=orders.aggregate(s=Sum("total_incl_tax"))["s"] or 0,
            avg_order_value=orders.aggregate(a=Avg("total_incl_tax"))["a"] or 0,
            total_searches=UserSearch.objects.count(),
            # Funnel
            funnel=[
                {"label": "Product views", "value": views, "pct": 100 if views else 0},
                {"label": "Added to basket", "value": baskets, "pct": _pct(baskets, views)},
                {"label": "Purchased", "value": purchases, "pct": _pct(purchases, views)},
            ],
            view_to_basket=_pct(baskets, views),
            basket_to_purchase=_pct(purchases, baskets),
            view_to_purchase=_pct(purchases, views),
            # Tables
            top_customers=UserRecord.objects.select_related("user").order_by("-total_spent")[:10],
            most_viewed=ProductRecord.objects.select_related("product")
            .filter(num_views__gt=0).order_by("-num_views")[:10],
            best_sellers=ProductRecord.objects.select_related("product")
            .filter(num_purchases__gt=0).order_by("-num_purchases")[:10],
            abandoned=ProductRecord.objects.select_related("product")
            .filter(num_basket_additions__gt=0, num_purchases=0)
            .order_by("-num_basket_additions")[:10],
            top_searches=UserSearch.objects.values("query")
            .annotate(n=Count("id")).order_by("-n")[:12],
            recent_views=UserProductView.objects.select_related("user", "product")
            .order_by("-date_created")[:15],
        )
        return ctx
