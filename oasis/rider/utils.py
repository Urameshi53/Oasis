from .models import RiderProfile


def make_user_a_rider(user, phone="", vehicle_type="motorbike"):
    """Turn a user into a delivery rider (idempotent)."""
    profile, _ = RiderProfile.objects.get_or_create(
        user=user,
        defaults={"phone": phone, "vehicle_type": vehicle_type},
    )
    return profile
