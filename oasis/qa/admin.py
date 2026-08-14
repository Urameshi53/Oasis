from django.contrib import admin

from .models import ProductAnswer, ProductQuestion


class AnswerInline(admin.TabularInline):
    model = ProductAnswer
    extra = 0


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "user", "body", "created_at")
    search_fields = ("product__title", "body", "user__username")
    inlines = [AnswerInline]
