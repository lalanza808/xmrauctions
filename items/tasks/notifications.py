from logging import getLogger
from huey import crontab
from huey.contrib.djhuey import periodic_task
from core.helpers.email_template import EmailTemplate
from items.models import Item


logger = getLogger('django.server')

@periodic_task(crontab(minute='0', hours='0', days='*/2'))
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