from logging import getLogger
from datetime import timedelta
from django.utils import timezone as tz
from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import periodic_task
from items.models import Item
from core.helpers.email_template import EmailTemplate


logger = getLogger('django.server')

@periodic_task(crontab(minute='0', hour='*/21'))
def close_stale_items():
    time_delta = tz.now() - timedelta(days=settings.ESCROW_PERIOD_DAYS)
    items = Item.objects.filter(list_date__lt=time_delta, available=True)

    for item in items:
        logger.info(f'[INFO] Found stale item #{item.id} (older than {settings.ESCROW_PERIOD_DAYS} days).')
        if item.bids:
            email_template = EmailTemplate(
                item=item,
                scenario='item_stale_with_bids',
                role='seller'
            )
            email_template.send()


