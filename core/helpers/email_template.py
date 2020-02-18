from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from items.models import Item
from sales.models import ItemSale


class EmailTemplate:
    def __init__(self, item, scenario, role):
        if isinstance(item, ItemSale):
            context = {
                'sale': item,
                'sale_path': reverse('get_sale', args=[item.id])
            }
            tpl_path = 'sales'
            if role == 'buyer':
                self.to_address = item.bid.bidder.email
            else:
                self.to_address = item.item.owner.email
        elif isinstance(item, Item):
            context = {
                'item': item,
                'item_path': reverse('get_item', args=[item.id])
            }
            tpl_path = 'items'
            self.to_address = item.owner.email

        context['site_name'] = settings.SITE_NAME
        context['site_url'] = settings.SITE_URL
        context['escrow_period'] = settings.ESCROW_PERIOD_DAYS
        context['stale_period'] = settings.STALE_PERIOD_DAYS

        subject = render_to_string(
            template_name=f'{tpl_path}/notify/{scenario}/{role}/subject.txt',
            context=context,
            request=None
        )
        body = render_to_string(
            template_name=f'{tpl_path}/notify/{scenario}/{role}/body.txt',
            context=context,
            request=None
        )
        self.subject = ''.join(subject.splitlines())
        self.body = body
        self.role = role
        self.item = item

    def send(self):
        res = send_mail(
            self.subject,
            self.body,
            settings.DEFAULT_FROM_EMAIL,
            [self.to_address]
        )
        return res