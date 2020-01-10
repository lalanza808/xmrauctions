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


class EmailTemplate:
    def __init__(self, item, scenario, role):
        context = {
            'sale': item,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'sale_path': reverse('get_sale', args=[item.bid.id]),
            'shipping_address': UserShippingAddress.objects.filter(
                user=item.bid.bidder
            ).first()
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


@periodic_task(crontab(minute='*/3'))
def notify_buyer_of_pending_sale():
    item_sales = ItemSale.objects.filter(buyer_notified=False)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            scenario='sale_created',
            role='buyer'
        )
        sent = email_template.send()
        if sent == 1:
            sale.buyer_notified = True
            sale.save()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/3'))
def notify_buyer_of_shipment_confirmation():
    item_sales = ItemSale.objects.filter(item_shipped=True).filter(buyer_notified_of_shipment=False)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            scenario='item_shipped',
            role='buyer'
        )
        sent = email_template.send()
        if sent == 1:
            sale.buyer_notified_of_shipment = True
            sale.save()
            bidder_profile = UserShippingAddress.objects.get(user=sale.bid.bidder)
            bidder_profile.delete()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/3'))
def notify_seller_of_shipment_receipt():
    item_sales = ItemSale.objects.filter(item_shipped=True, item_received=False).filter(seller_notified_of_receipt=False)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            scenario='item_shipped',
            role='buyer'
        )
        sent = email_template.send()
        if sent == 1:
            sale.seller_notified_of_receipt = True
            sale.save()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/5'))
def notify_seller_of_funds_received():
    item_sales = ItemSale.objects.filter(seller_notified=False, buyer_notified=True).filter(payment_received=True)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            scenario='funds_received',
            role='seller'
        )
        sent = email_template.send()
        if sent == 1:
            sale.seller_notified = True
            sale.save()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/30'))
def pay_sellers_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        return False

    item_sales = ItemSale.objects.filter(item_received=True, payment_received=True).filter(seller_paid=False)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            scenario='sale_completed',
            role='seller'
        )

        if sale.seller_notified_of_payout is False:
            sent = email_template.send()
            sale.seller_notified_of_payout = True
            sale.save()

        try:
            txs = aw.wallet.accounts[sale.escrow_account_index].transfer(
                sale.item.payout_address, sale.agreed_price_xmr, relay=True
            )
            if txs:
                sale.seller_paid = True
                sale.escrow_complete = True
                sale.save()
                return True
            else:
                return False
        except Exception as e:
            print('unable to make payment: ', e)
            return False

@periodic_task(crontab(hour='*/6'))
def pay_platform_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        return False

    aof = settings.PLATFORM_WALLET_ADDRESS
    if aof is None:
        aof = aw.wallet.accounts[0].address()

    item_sales = ItemSale.objects.filter(escrow_complete=True, seller_paid=True, item_received=True).filter(platform_paid=False)
    for sale in item_sales:
        try:
            txs = aw.wallet.accounts[sale.escrow_account_index].sweep_all(aof)
            if txs:
                sale.platform_paid = True
                sale.sale_finalized = True
                sale.save()
                return True
        except Exception as e:
            print('unable to sweep funds: ', e)
            return False


@periodic_task(crontab(minute='*/3'))
def poll_for_buyer_escrow_payments():
    aw = AuctionWallet()
    if aw.connected is False:
        return False

    item_sales = ItemSale.objects.filter(payment_received=False)
    for sale in item_sales:
        sale_account = aw.wallet.accounts[sale.escrow_account_index]

        sale.received_payment_xmr = sale_account.balance()

        if sale_account.balance() >= Decimal(str(sale.expected_payment_xmr)):
            sale.payment_received = True

        sale.save()

        if settings.DEBUG:
            print('[+] Sale: #{} - Balance: {} - Payment Received: {}'.format(
                sale.id, sale.received_payment_xmr, sale.payment_received
            ))

# TODO - close out old sales
