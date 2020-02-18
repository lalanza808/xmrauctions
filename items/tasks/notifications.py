from logging import getLogger
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.conf import settings
from core.helpers.email_template import EmailTemplate
from items.models import Item
from items.tasks.common import get_items_past_days


logger = getLogger('django.server')

@periodic_task(crontab(minute='0', hour='0', day='*/2'))
def notify_seller_of_item_bids():
    items = Item.objects.all()
    for item in items:
        if len(item.bids.all()) > 0:
            logger.info(f'[INFO] Item #{item.id} has some bids. Notifying the seller.')
            email_template = EmailTemplate(
                item=item,
                scenario='item_has_bids',
                role='seller'
            )
            email_template.send()

@periodic_task(crontab(minute='0', hour='0', day='*/3'))
def notify_seller_of_stale_items():
    stale_days = settings.ESCROW_PERIOD_DAYS - 7
    items = get_items_past_days(stale_days)
    for item in items:
        logger.info(f'[INFO] Found stale item #{item.id} (older than {stale_days} days).')
        if item.bids:
            email_template = EmailTemplate(
                item=item,
                scenario='item_stale_with_bids',
                role='seller'
            )
            email_template.send()
