from django import template
from django.db.models import Q

register = template.Library()


@register.simple_tag
def thread_unread(thread, user):
    """Unread message count in a thread for this user."""
    return thread.unread_count_for(user)


@register.simple_tag
def other_party(thread, user):
    """Label of the person `user` is talking to in this thread."""
    return thread.other_party_label(user)


@register.simple_tag
def unread_message_count(user):
    """Total unread messages across all threads the user is part of."""
    if not user or not user.is_authenticated:
        return 0
    from messaging.models import Message

    return (
        Message.objects.filter(
            Q(thread__buyer=user) | Q(thread__partner__users=user),
            is_read=False,
        )
        .exclude(sender=user)
        .count()
    )
