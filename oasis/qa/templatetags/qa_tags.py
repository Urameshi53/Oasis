from django import template

register = template.Library()


@register.simple_tag
def top_questions(product, limit=3):
    """Most recent questions for a product, with answers prefetched."""
    return list(
        product.questions.prefetch_related("answers", "answers__user")[:limit]
    )


@register.simple_tag
def question_count(product):
    return product.questions.count()
