from django import template

from membership.models import user_is_member

register = template.Library()


@register.simple_tag
def is_member(user):
    return user_is_member(user)
