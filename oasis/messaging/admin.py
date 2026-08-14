from django.contrib import admin

from .models import Message, MessageThread


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "partner", "subject", "updated_at")
    search_fields = ("buyer__username", "partner__name", "subject")
    inlines = [MessageInline]
