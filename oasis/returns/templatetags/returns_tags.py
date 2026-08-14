from django import template

from returns.utils import can_return_order, returnable_qty

register = template.Library()


@register.simple_tag
def can_return(user, order):
    return can_return_order(user, order)


@register.simple_tag
def line_returnable_qty(order_line):
    return returnable_qty(order_line)
