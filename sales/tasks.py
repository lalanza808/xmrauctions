import logging
from decimal import Decimal
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from core.monero import AuctionWallet
from core.models import UserShippingAddress
from sales.models import ItemSale


logger = logging.getLogger('django.server')

class EmailTemplate:
    def __init__(self, item, scenario, role):
        context = {
            'sale': item,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'sale_path': reverse('get_sale', args=[item.id])
        }
        subject = render_to_string(
            template_name=f'sales/notify/{scenario}/{role}/subject.txt',
            context=context,
            request=None
        )
        body = render_to_string(
            template_name=f'sales/notify/{scenario}/{role}/body.txt',
            context=context,
            request=None
        )
        self.subject = ''.join(subject.splitlines())
        self.body = body
        self.role = role
        self.item = item

    def send(self):
        if self.role == 'buyer':
            to_address = self.item.bid.bidder.email
        else:
            to_address = self.item.item.owner.email

        res = send_mail(
            self.subject,
            self.body,
            settings.DEFAULT_FROM_EMAIL,
            [to_address]
        )
        return res


### Notifications


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


### Payments

@periodic_task(crontab(minute='*'))
def poll_for_buyer_escrow_payments():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(payment_received=False)
    for sale in item_sales:
        logger.info(f'[INFO] Polling escrow address #{sale.escrow_account_index} for sale #{sale.id} for new funds.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
        unlocked = sale_account.balances()[1]
        sale.received_payment_xmr = unlocked
        if unlocked >= Decimal(str(sale.expected_payment_xmr)):
            logger.info(f'[INFO] Found payment of {sale.received_payment_xmr} XMR for sale #{sale.id}.')
            sale.payment_received = True

        sale.save()


@periodic_task(crontab(minute='*'))
def pay_sellers_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(item_received=True, payment_received=True).filter(seller_paid=False)
    for sale in item_sales:
        # Take platform fees from the sale - the 50:50 split between buyer/seller
        sale_total = sale.agreed_price_xmr - sale.platform_fee_xmr
        sale_account = aw.wallet.accounts[sale.escrow_account_index]

        if sale_account.balances()[1] >= Decimal(sale.agreed_price_xmr):
            try:
                # Construct a transaction so we can get current fee and subtract from the total
                _tx = sale_account.transfer(
                    sale.item.payout_address, Decimal(.01), relay=False
                )
                new_total = sale_total - float(_tx[0].fee)

                logger.info(f'[INFO] Sending {new_total} XMR from wallet account #{sale.escrow_account_index} to item owner\'s payout address for sale #{sale.id}.')
                # Make the transaction with network fee removed
                tx = sale_account.transfer(
                    sale.item.payout_address, new_total, relay=True
                )
                sale.network_fee_xmr = _tx[0].fee
                sale.seller_payout_transaction = tx[0]
                sale.seller_paid = True
                sale.escrow_complete = True
                sale.save()
            except Exception as e:
                logger.error(f'[ERROR] Unable to pay seller for sale #{sale.id}: ')
        else:
            logger.warning(f'[WARNING] Not enough unlocked funds available in account #{sale.escrow_account_index} for sale #{sale.id}.')

        if sale.seller_paid and sale.seller_notified_of_payout is False:
            email_template = EmailTemplate(
                item=sale,
                scenario='sale_completed',
                role='seller'
            )
            sent = email_template.send()
            sale.seller_notified_of_payout = True
            sale.save()

@periodic_task(crontab(minute='*/30'))
def pay_platform_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('Auction wallet is not connected. Quitting.')
        return False

    aof = settings.PLATFORM_WALLET_ADDRESS
    if aof is None:
        aof = str(aw.wallet.accounts[0].address())

    item_sales = ItemSale.objects.filter(escrow_complete=True, seller_paid=True, item_received=True).filter(platform_paid=False)
    for sale in item_sales:
        logger.info(f'[INFO] Paying platform fees for sale #{sale.id} to wallet {aof}.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
        bal = sale_account.balances()[1]
        if bal >= 0:
            try:
                if settings.PLATFORM_FEE_PERCENT > 0:
                    logger.info(f'[INFO] Getting platform fees of {bal} XMR')
                    sale_account.sweep_all(aof)
                else:
                    logging.info('No platform fees are set - proceeding without taking fees.')

                sale.platform_paid = True
                sale.sale_finalized = True
                sale.save()
                return True
            except Exception as e:
                logger.error(f'[ERROR] Unable to pay platform for sale #{sale.id} - trying again')
        else:
            logger.warning(f'[WARNING] Not enough unlocked funds available in account #{sale.escrow_account_index} for sale #{sale.id}.')

@periodic_task(crontab(minute='0', hour='*/12'))
def close_completed_items_sales():
    item_sales = ItemSale.objects.filter(platform_paid=True, sale_finalized=True)
    for sale in item_sales:
        logger.info(f'[INFO] Deleting item #{sale.item.id} and all accompanying bids, sales, meta, etc.')
        sale.item.delete()

@periodic_task(crontab(minute='*'))
def closed_cancelled_sales():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(sale_cancelled=True)
    for sale in item_sales:
        logger.info(f'[INFO] Deleting sale #{sale.id} and transferring back any sent funds to the buyer.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
        if sale_account.balances()[0] > Decimal(0.0):
            try:
                sale_account.sweep_all(sale.bid.return_address)
                sale.delete()
            except Exception as e:
                logger.error(f'[ERROR] Unable to return funds to use for sale #{sale.id}.')
        else:
            sale.delete()
