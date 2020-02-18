from logging import getLogger
from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import periodic_task
from items.tasks.common import get_items_past_days


logger = getLogger('django.server')

@periodic_task(crontab(minute='0', hour='0', day='*'))
def delete_expired_items():
    expired_days = settings.ESCROW_PERIOD_DAYS
    items = get_items_past_days(expired_days)
    for item in items:
        logger.info(f'[INFO] Found expired item #{item.id} (older than {expired_days} days).')
        item.delete()
