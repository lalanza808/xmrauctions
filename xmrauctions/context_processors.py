from django.conf import settings


def inject_site_meta(request):
    return {
        'site_meta': {
            'debug': settings.DEBUG,
            'name': settings.SITE_NAME,
            'donation_address': settings.DONATION_WALLET_ADDRESS,
            'platform_address': settings.PLATFORM_WALLET_ADDRESS
        }
    }
