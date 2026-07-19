from django.contrib import admin

from .models import Delivery, RiderProfile


@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "vehicle_type", "is_available", "created_at")
    search_fields = ("user__username", "user__email", "phone")


@admin.action(description="Mark selected deliveries as paid out")
def mark_paid_out(modeladmin, request, queryset):
    updated = queryset.update(payout_status=Delivery.PAYOUT_PAID)
    modeladmin.message_user(request, f"{updated} delivery payout(s) marked paid.")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "order", "rider", "status", "fee", "payout_status", "delivered_at", "created_at",
    )
    list_filter = ("status", "payout_status")
    search_fields = ("order__number", "rider__user__username")
    autocomplete_fields = ("rider",)
    actions = [mark_paid_out]
