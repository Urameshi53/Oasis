from django.contrib import admin

from .models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "started_at", "expires_at", "price")
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__email")
