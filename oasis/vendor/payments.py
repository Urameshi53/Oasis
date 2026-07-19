"""
Marketplace split-payment logic.

Given a placed order that may contain items from several vendors, this module
works out how much each vendor earns (after platform commission) and how to
tell Paystack to route the money to each vendor's subaccount.

The pure calculation functions (``split_order_by_partner``) need no network or
keys and are fully unit-testable. The Paystack helpers only make live calls when
``PAYSTACK_SECRET_KEY`` is configured.
"""

from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

import requests
from django.conf import settings

TWOPLACES = Decimal("0.01")


def _money(value):
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _profile_for(partner):
    return getattr(partner, "vendor_profile", None)


def _commission_rate_for(partner):
    profile = _profile_for(partner)
    if profile is not None:
        return profile.effective_commission_rate
    return Decimal(str(getattr(settings, "PLATFORM_COMMISSION_RATE", 10)))


def split_order_by_partner(order):
    """
    Group an order's lines by vendor (Partner) and compute each vendor's share.

    Returns a list of dicts, one per partner::

        {partner, gross, commission, net, rate, currency, subaccount}

    ``gross`` is what the customer paid for that vendor's lines; ``commission``
    is the platform's cut; ``net`` is what the vendor is owed. Shipping and any
    line with no partner are left with the platform (not attributed to a vendor).
    """
    buckets = OrderedDict()
    for line in order.lines.all():
        partner = line.partner
        if partner is None:
            continue
        buckets.setdefault(partner.pk, {"partner": partner, "gross": Decimal("0")})
        buckets[partner.pk]["gross"] += Decimal(line.line_price_incl_tax)

    results = []
    for data in buckets.values():
        partner = data["partner"]
        gross = _money(data["gross"])
        rate = _commission_rate_for(partner)
        commission = _money(gross * rate / Decimal("100"))
        profile = _profile_for(partner)
        results.append(
            {
                "partner": partner,
                "gross": gross,
                "commission": commission,
                "net": _money(gross - commission),
                "rate": rate,
                "currency": order.currency,
                "subaccount": getattr(profile, "paystack_subaccount_code", "") or "",
            }
        )
    return results


def record_vendor_sales(order):
    """
    Create a :class:`VendorSale` ledger row per vendor in the order (idempotent
    via ``get_or_create`` on the ``(order, partner)`` unique constraint).
    Returns the list of VendorSale rows.
    """
    from .models import VendorSale

    rows = []
    for share in split_order_by_partner(order):
        row, _ = VendorSale.objects.get_or_create(
            order=order,
            partner=share["partner"],
            defaults={
                "gross": share["gross"],
                "commission": share["commission"],
                "net": share["net"],
                "commission_rate": share["rate"],
                "currency": share["currency"],
            },
        )
        rows.append(row)
    return rows


def build_paystack_split(order):
    """
    Build the inline Paystack ``split`` payload for an order so that each
    vendor's ``net`` settles to their subaccount and the platform keeps the
    remainder (commission + shipping). Vendors without a subaccount code are
    skipped — their share stays with the platform account.

    Returns ``None`` if no vendor has a subaccount configured (nothing to split).
    """
    subaccounts = []
    for share in split_order_by_partner(order):
        code = share["subaccount"]
        if not code or share["net"] <= 0:
            continue
        subaccounts.append(
            {"subaccount": code, "share": int((share["net"] * 100).to_integral_value())}
        )

    if not subaccounts:
        return None

    return {
        "type": "flat",
        "currency": order.currency,
        "bearer_type": "account",  # platform (main account) bears the Paystack fee
        "subaccounts": subaccounts,
    }


# --- Paystack API helpers (only used when keys are configured) ---------------


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def create_subaccount(business_name, settlement_bank, account_number, percentage_charge):
    """
    Create a Paystack subaccount for a vendor and return the API response.

    ``percentage_charge`` is the percentage the SUBACCOUNT (vendor) keeps on a
    transaction when used via the simple ``subaccount`` param; for multi-vendor
    flat splits we compute exact shares ourselves instead.
    """
    if not settings.PAYSTACK_SECRET_KEY:
        raise RuntimeError("PAYSTACK_SECRET_KEY is not configured.")
    payload = {
        "business_name": business_name,
        "settlement_bank": settlement_bank,
        "account_number": account_number,
        "percentage_charge": percentage_charge,
    }
    resp = requests.post(
        f"{settings.PAYSTACK_BASE_URL}/subaccount", json=payload, headers=_headers()
    )
    return resp.json()


def initialize_split_payment(email, order, reference, callback_url):
    """
    Initialise a Paystack transaction for a marketplace order, including the
    per-vendor split when subaccounts are configured. Returns the API response.
    """
    if not settings.PAYSTACK_SECRET_KEY:
        raise RuntimeError("PAYSTACK_SECRET_KEY is not configured.")
    amount = Decimal(order.total_incl_tax)
    data = {
        "email": email,
        "amount": int((amount * 100).to_integral_value()),  # pesewas/kobo
        "reference": reference,
        "callback_url": callback_url,
    }
    split = build_paystack_split(order)
    if split is not None:
        data["split"] = split
    resp = requests.post(
        settings.PAYSTACK_INITIALIZE_URL, json=data, headers=_headers()
    )
    return resp.json()
