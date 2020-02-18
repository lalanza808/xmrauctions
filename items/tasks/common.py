from datetime import timedelta
from django.utils import timezone as tz
from django.conf import settings
from items.models import Item


def get_items_past_days(days=settings.ESCROW_PERIOD_DAYS) -> list:
    time_delta = tz.now() - timedelta(days=days)
    items = Item.objects.filter(list_date__lt=time_delta, available=True)
    return items
