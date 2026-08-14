from django.contrib import messages as flash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from oscar.core.loading import get_model

from .models import Message, MessageThread

Partner = get_model("partner", "Partner")
Product = get_model("catalogue", "Product")
Order = get_model("order", "Order")


def _notify_thread(thread, sender, body):
    """Notify the party who did NOT send this message."""
    try:
        from notifications.utils import notify, notify_many

        url = reverse("messaging:thread", args=[thread.pk])
        preview = (body[:60] + "…") if len(body) > 60 else body
        if sender.id == thread.buyer_id:
            # buyer -> seller(s)
            recipients = list(thread.partner.users.all())
            notify_many(
                recipients,
                "New message from %s: %s" % (sender.get_username(), preview),
                url=url,
                icon="bi-chat-dots",
                level="info",
            )
        else:
            notify(
                thread.buyer,
                "%s replied: %s" % (thread.partner.display_name, preview),
                url=url,
                icon="bi-chat-dots",
                level="info",
            )
    except Exception:
        pass


class InboxView(LoginRequiredMixin, ListView):
    """All threads the user takes part in, as buyer or as seller."""

    template_name = "oscar/messaging/inbox.html"
    context_object_name = "threads"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        return (
            MessageThread.objects.filter(Q(buyer=user) | Q(partner__users=user))
            .distinct()
            .select_related("partner", "buyer", "product", "order")
            .prefetch_related("messages")
        )


class ThreadView(LoginRequiredMixin, View):
    """View a conversation and post a reply."""

    template_name = "oscar/messaging/thread.html"

    def get_thread(self):
        thread = get_object_or_404(MessageThread, pk=self.kwargs["pk"])
        if not thread.is_participant(self.request.user):
            raise PermissionDenied
        return thread

    def get(self, request, *args, **kwargs):
        thread = self.get_thread()
        thread.mark_read_for(request.user)
        return render(request, self.template_name, {"thread": thread})

    def post(self, request, *args, **kwargs):
        thread = self.get_thread()
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(thread=thread, sender=request.user, body=body)
            thread.touch()
            _notify_thread(thread, request.user, body)
        return redirect("messaging:thread", pk=thread.pk)


class ContactSellerView(LoginRequiredMixin, View):
    """
    Start (or continue) a conversation with a seller, optionally anchored to a
    product or order. Buyers only — a seller can't message their own store.
    """

    template_name = "oscar/messaging/contact.html"

    def _resolve(self):
        partner = get_object_or_404(Partner, code=self.kwargs["code"])
        product = None
        order = None
        pk = self.request.GET.get("product") or self.request.POST.get("product")
        num = self.request.GET.get("order") or self.request.POST.get("order")
        if pk:
            product = Product.objects.filter(pk=pk).first()
        if num:
            order = Order.objects.filter(number=num, user=self.request.user).first()
        return partner, product, order

    def get(self, request, *args, **kwargs):
        partner, product, order = self._resolve()
        return render(
            request,
            self.template_name,
            {"partner": partner, "product": product, "order": order},
        )

    def post(self, request, *args, **kwargs):
        partner, product, order = self._resolve()
        body = request.POST.get("body", "").strip()
        if not body:
            flash.error(request, "Please type a message.")
            return redirect(request.get_full_path())

        if partner.users.filter(pk=request.user.pk).exists():
            flash.error(request, "You can't message your own store.")
            return redirect("catalogue:index")

        # Reuse an existing thread for the same buyer+seller+context.
        lookup = {"buyer": request.user, "partner": partner}
        if order:
            lookup["order"] = order
        elif product:
            lookup["product"] = product
        thread = MessageThread.objects.filter(**lookup).first()
        if thread is None:
            subject = (
                "Re: order %s" % order.number
                if order
                else (product.get_title() if product else "General enquiry")
            )
            thread = MessageThread.objects.create(
                buyer=request.user,
                partner=partner,
                product=product,
                order=order,
                subject=subject,
            )

        Message.objects.create(thread=thread, sender=request.user, body=body)
        thread.touch()
        _notify_thread(thread, request.user, body)
        flash.success(request, "Message sent to %s." % partner.display_name)
        return redirect("messaging:thread", pk=thread.pk)
