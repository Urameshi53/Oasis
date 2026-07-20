from .models import Notification


def notify(user, message, url="", icon="bell", level=Notification.INFO):
    """Create a single notification (no-op if user is falsy)."""
    if not user:
        return None
    return Notification.objects.create(
        recipient=user, message=message, url=url, icon=icon, level=level
    )


def notify_many(users, message, url="", icon="bell", level=Notification.INFO):
    """Create the same notification for many users in one query."""
    objs = [
        Notification(recipient=u, message=message, url=url, icon=icon, level=level)
        for u in users
        if u is not None
    ]
    if objs:
        Notification.objects.bulk_create(objs)
    return objs
