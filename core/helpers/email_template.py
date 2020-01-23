from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


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