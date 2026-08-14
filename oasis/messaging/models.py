"""
Buyer <-> seller messaging.

A ``MessageThread`` is a conversation between one buyer and one seller (an
Oscar ``Partner``), optionally anchored to a product or an order. Either party
posts ``Message`` rows; ``is_read`` tracks whether the *other* party has seen a
message yet, which drives unread badges.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class MessageThread(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_threads"
    )
    partner = models.ForeignKey(
        "partner.Partner", on_delete=models.CASCADE, related_name="message_threads"
    )
    subject = models.CharField(max_length=200, blank=True)
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_threads",
    )
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_threads",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Thread #{self.pk}: {self.buyer} ↔ {self.partner.display_name}"

    def is_participant(self, user):
        if not user.is_authenticated:
            return False
        return (
            user.id == self.buyer_id
            or user.is_staff
            or self.partner.users.filter(pk=user.pk).exists()
        )

    def is_seller_side(self, user):
        """True if `user` acts as the seller in this thread (not the buyer)."""
        return user.id != self.buyer_id

    def other_party_label(self, user):
        """Human label for the person `user` is talking to."""
        if self.is_seller_side(user):
            return self.buyer.get_full_name() or self.buyer.get_username()
        return self.partner.display_name

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def mark_read_for(self, user):
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    def touch(self):
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])


class Message(models.Model):
    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Message #{self.pk} from {self.sender} in thread {self.thread_id}"
