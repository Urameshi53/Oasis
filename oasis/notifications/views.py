from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.timesince import timesince
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationFeedView(LoginRequiredMixin, View):
    """Lightweight JSON feed the header polls for live updates."""

    def get(self, request):
        qs = request.user.app_notifications.all()
        unread = qs.filter(is_read=False).count()
        items = [
            {
                "id": n.id,
                "message": n.message,
                "icon": n.icon or "bell",
                "level": n.level,
                "is_read": n.is_read,
                "ago": timesince(n.created_at).split(",")[0] + " ago",
                "url": reverse("notifications:open", kwargs={"pk": n.id}),
            }
            for n in qs[:8]
        ]
        return JsonResponse({"unread": unread, "items": items})


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "oscar/notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 30

    def get_queryset(self):
        return self.request.user.app_notifications.all()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Render with the original read/unread state, THEN mark everything read
        # so the bell count clears on the next page load.
        response.render()
        request.user.app_notifications.filter(is_read=False).update(is_read=True)
        return response


class OpenNotificationView(LoginRequiredMixin, View):
    """Mark one notification read and forward to its target URL."""

    def get(self, request, pk):
        note = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not note.is_read:
            note.is_read = True
            note.save(update_fields=["is_read"])
        return redirect(note.url or "notifications:list")


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.app_notifications.filter(is_read=False).update(is_read=True)
        return redirect("notifications:list")
