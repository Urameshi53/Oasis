from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

#: Payouts to sellers and riders run at this hour, on the next working day.
PAYOUT_HOUR = 10


def next_payout_datetime(now=None):
    """
    Return the datetime of the next payout run: 10:00 AM on the next working
    day (Mon–Fri; weekends roll to Monday).
    """
    if now is None:
        now = timezone.now()
    if timezone.is_aware(now):
        now = timezone.localtime(now)

    day = now.date() + timedelta(days=1)
    while day.weekday() >= 5:  # Saturday = 5, Sunday = 6
        day += timedelta(days=1)

    dt = datetime.combine(day, time(PAYOUT_HOUR, 0))
    if settings.USE_TZ:
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt
