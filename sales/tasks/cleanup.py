import logging
from huey import crontab
from huey.contrib.djhuey import periodic_task

logger = logging.getLogger('django.server')

@periodic_task(crontab(minute='0', hour='*/12'))
def close_completed_items_sales():
    item_sales = ItemSale.objects.filter(platform_paid=True, sale_finalized=True)
    for sale in item_sales:
        logger.info(f'[INFO] Deleting item #{sale.item.id} and all accompanying bids, sales, meta, etc.')
        sale.item.delete()