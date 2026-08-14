from django.contrib import admin

from .models import ReturnLine, ReturnRequest


class ReturnLineInline(admin.TabularInline):
    model = ReturnLine
    extra = 0


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "user", "status", "reason", "refund_amount", "created_at")
    list_filter = ("status", "reason")
    search_fields = ("order__number", "user__username", "user__email")
    inlines = [ReturnLineInline]
    date_hierarchy = "created_at"
