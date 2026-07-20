def notifications(request):
    """Expose the current user's unread count + recent notifications to the header."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    qs = user.app_notifications.all()
    return {
        "notif_unread_count": qs.filter(is_read=False).count(),
        "notif_recent": list(qs[:6]),
    }
