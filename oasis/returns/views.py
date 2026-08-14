from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from oscar.core.loading import get_model

from .models import ReturnLine, ReturnRequest
from .utils import can_return_order, returnable_lines, returnable_qty

Order = get_model("order", "Order")


class ReturnCreateView(LoginRequiredMixin, View):
    """Customer opens a return against one of their delivered orders."""

    template_name = "oscar/returns/return_create.html"

    def get_order(self):
        return get_object_or_404(Order, number=self.kwargs["order_number"], user=self.request.user)

    def get(self, request, *args, **kwargs):
        order = self.get_order()
        if not can_return_order(request.user, order):
            messages.warning(request, "This order isn't eligible for a return.")
            return redirect("customer:order", order_number=order.number)
        return render(request, self.template_name, self._context(order))

    def _context(self, order):
        lines = []
        for line in returnable_lines(order):
            lines.append({"line": line, "max_qty": returnable_qty(line)})
        return {
            "order": order,
            "lines": lines,
            "reasons": ReturnRequest.REASON_CHOICES,
        }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        order = self.get_order()
        if not can_return_order(request.user, order):
            raise PermissionDenied

        reason = request.POST.get("reason") or "other"
        comment = request.POST.get("comment", "").strip()

        selected = []
        for line in returnable_lines(order):
            if request.POST.get("line_%d" % line.id):
                try:
                    qty = int(request.POST.get("qty_%d" % line.id, 1))
                except (TypeError, ValueError):
                    qty = 1
                qty = max(1, min(qty, returnable_qty(line)))
                selected.append((line, qty))

        if not selected:
            messages.error(request, "Select at least one item to return.")
            return render(request, self.template_name, self._context(order))

        rr = ReturnRequest.objects.create(
            order=order,
            user=request.user,
            reason=reason,
            comment=comment,
            currency=order.currency,
        )
        for line, qty in selected:
            ReturnLine.objects.create(return_request=rr, order_line=line, quantity=qty)
        rr.refund_amount = rr.expected_refund()
        rr.save(update_fields=["refund_amount"])

        self._notify_sellers(rr)
        messages.success(request, "Your return request has been submitted.")
        return redirect("returns:detail", pk=rr.pk)

    def _notify_sellers(self, rr):
        try:
            from notifications.utils import notify

            url = reverse("returns:seller-list")
            for partner in rr.partners():
                for seller in partner.users.all():
                    notify(
                        seller,
                        "New return request for order %s." % rr.order.number,
                        url=url,
                        icon="bi-arrow-return-left",
                        level="warning",
                    )
        except Exception:
            pass


class ReturnListView(LoginRequiredMixin, ListView):
    """Customer's own returns."""

    template_name = "oscar/returns/return_list.html"
    context_object_name = "returns"
    paginate_by = 20

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user).prefetch_related("lines")


class ReturnDetailView(LoginRequiredMixin, DetailView):
    """Visible to the owner, an involved seller, or staff."""

    template_name = "oscar/returns/return_detail.html"
    context_object_name = "return_request"

    def get_object(self, queryset=None):
        rr = get_object_or_404(ReturnRequest, pk=self.kwargs["pk"])
        if rr.user_id != self.request.user.id and not rr.can_be_managed_by(self.request.user):
            raise PermissionDenied
        return rr

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_manage"] = self.object.can_be_managed_by(self.request.user)
        return ctx


class SellerReturnListView(LoginRequiredMixin, ListView):
    """Returns that include the seller's products."""

    template_name = "oscar/returns/seller_list.html"
    context_object_name = "returns"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.partners.exists()
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        qs = ReturnRequest.objects.prefetch_related("lines").select_related("order", "user")
        if user.is_staff:
            return qs
        return qs.filter(lines__order_line__partner__users=user).distinct()


class ReturnActionView(LoginRequiredMixin, View):
    """Seller/staff approve, reject or refund a return."""

    def post(self, request, *args, **kwargs):
        rr = get_object_or_404(ReturnRequest, pk=kwargs["pk"])
        if not rr.can_be_managed_by(request.user):
            raise PermissionDenied

        action = request.POST.get("action")
        note = request.POST.get("note", "").strip()

        if action == "approve" and rr.status == ReturnRequest.REQUESTED:
            rr.approve(note)
            messages.success(request, "Return approved.")
        elif action == "reject" and rr.status == ReturnRequest.REQUESTED:
            rr.reject(note)
            messages.success(request, "Return declined.")
        elif action == "refund" and rr.status == ReturnRequest.APPROVED:
            rr.mark_refunded()
            messages.success(request, "Refund recorded and stock returned.")
        else:
            messages.error(request, "That action isn't available for this return.")

        return redirect(request.POST.get("next") or reverse("returns:detail", args=[rr.pk]))


class ReturnCancelView(LoginRequiredMixin, View):
    """Customer cancels their own still-open request."""

    def post(self, request, *args, **kwargs):
        rr = get_object_or_404(ReturnRequest, pk=kwargs["pk"], user=request.user)
        if rr.status == ReturnRequest.REQUESTED:
            rr.status = ReturnRequest.CANCELLED
            rr.save(update_fields=["status", "updated_at"])
            messages.success(request, "Return request cancelled.")
        return redirect("returns:detail", pk=rr.pk)
