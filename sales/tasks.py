from decimal import Decimal
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from core.monero import AuctionWallet
from sales.models import ItemSale


class EmailTemplate:
    def __init__(self, item, role):
        context = {
            'sale': item,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'sale_path': reverse('get_sale', args=[item.bid.id])
        }
        subject = render_to_string(
            template_name=f'sales/notify/{role}/subject.txt',
            context=context,
            request=None
        )
        body = render_to_string(
            template_name=f'sales/notify/{role}/body.txt',
            context=context,
            request=None
        )
        self.subject = ''.join(subject.splitlines())
        self.body = body


@periodic_task(crontab(minute='*/3'))
def notify_buyer_of_pending_sale():
    item_sales = ItemSale.objects.filter(buyer_notified=False)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            role='buyer'
        )
        sent = send_mail(
            email_template.subject,
            email_template.body,
            settings.EMAIL_FROM,
            [sale.bid.bidder.email]
        )
        if sent == 1:
            sale.buyer_notified = True
            sale.save()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/2'))
def notify_seller_of_funds_received():
    item_sales = ItemSale.objects.filter(seller_notified=False, buyer_notified=True, payment_received=True)
    for sale in item_sales:
        email_template = EmailTemplate(
            item=sale,
            role='seller'
        )
        sent = send_mail(
            email_template.subject,
            email_template.body,
            settings.EMAIL_FROM,
            [sale.item.owner.email]
        )
        if sent == 1:
            sale.seller_notified = True
            sale.save()
            return True
        else:
            return False

@periodic_task(crontab(minute='*/10'))
def poll_for_buyer_escrow_payments():
    aw = AuctionWallet()
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
