from django.contrib.auth.models import Permission

from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")


def get_or_create_profile(partner):
    """Return the vendor's :class:`VendorProfile`, creating a blank one if needed."""
    from .models import VendorProfile

    profile, _ = VendorProfile.objects.get_or_create(partner=partner)
    return profile


def get_dashboard_access_permission():
    """Return the ``partner.dashboard_access`` permission used to gate the
    Oscar dashboard for non-staff (vendor) users."""
    return Permission.objects.get(
        codename="dashboard_access",
        content_type__app_label="partner",
    )


def make_user_a_seller(user, shop_name):
    """
    Turn a regular user into a marketplace vendor.

    Creates a :class:`Partner` (Oscar's vendor/fulfilment entity), links the
    user to it, and grants the dashboard-access permission so they can manage
    their own products and orders from ``/dashboard/``.

    Returns the created ``Partner``.
    """
    partner = Partner.objects.create(name=shop_name)
    partner.users.add(user)
    user.user_permissions.add(get_dashboard_access_permission())
    get_or_create_profile(partner)
    return partner
