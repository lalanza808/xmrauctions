import logging
from huey import crontab
from huey.contrib.djhuey import periodic_task
from core.helpers.email_template import EmailTemplate
from core.models import UserShippingAddress
from sales.models import ItemSale


logger = logging.getLogger('django.server')

@periodic_task(crontab(minute='*'))
def notify_buyer_of_pending_sale():
    item_sales = ItemSale.objects.filter(buyer_notified=False, sale_cancelled=False)
    for sale in item_sales:
        logger.info(f'[INFO] Sale #{sale.id} just created, notifying buyer.')
        email_template = EmailTemplate(
            item=sale,
            scenario='sale_created',
            role='buyer'
        )
        email_template.send()
        sale.buyer_notified = True
        sale.save()

@periodic_task(crontab(minute='*'))
def notify_seller_of_funds_received():
    item_sales = ItemSale.objects.filter(seller_notified=False, buyer_notified=True).filter(payment_received=True)
    for sale in item_sales:
        logger.info(f'[INFO] Funds received from buyer for sale #{sale.id}, notifying seller.')
        email_template = EmailTemplate(
            item=sale,
            scenario='funds_received',
            role='seller'
        )
        email_template.send()
        sale.seller_notified = True
        sale.save()

@periodic_task(crontab(minute='*'))
def notify_buyer_of_shipment_confirmation():
    item_sales = ItemSale.objects.filter(item_shipped=True).filter(buyer_notified_of_shipment=False)
    for sale in item_sales:
        logger.info(f'[INFO] Item shipped for sale #{sale.id}, notifying buyer.')
        email_template = EmailTemplate(
            item=sale,
            scenario='item_shipped',
            role='buyer'
        )
        email_template.send()
        bidder_profile = UserShippingAddress.objects.get(user=sale.bid.bidder)
        bidder_profile.delete()
        logger.info(f'[INFO] Buyer shipping info wiped for sale #{sale.id}')
        sale.buyer_notified_of_shipment = True
        sale.save()
