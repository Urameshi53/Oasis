from django.contrib import admin

from .models import VendorProfile, VendorSale


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("partner", "tagline", "commission_rate", "created_at")
    search_fields = ("partner__name", "tagline")


@admin.action(description="Mark selected sales as paid out")
def mark_as_paid(modeladmin, request, queryset):
    updated = queryset.update(status=VendorSale.PAID)
    modeladmin.message_user(request, f"{updated} sale(s) marked as paid out.")


@admin.action(description="Mark selected sales as pending")
def mark_as_pending(modeladmin, request, queryset):
    updated = queryset.update(status=VendorSale.PENDING)
    modeladmin.message_user(request, f"{updated} sale(s) marked as pending.")


@admin.register(VendorSale)
class VendorSaleAdmin(admin.ModelAdmin):
    list_display = ("order", "partner", "gross", "commission", "net", "status", "created_at")
    list_filter = ("status", "partner")
    search_fields = ("order__number", "partner__name")
    actions = [mark_as_paid, mark_as_pending]
