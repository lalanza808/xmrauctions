from django.conf import settings


def inject_site_meta(request):
    return {
        'site_meta': {
            'debug': settings.DEBUG,
            'name': settings.SITE_NAME,
            'escrow_period': settings.ESCROW_PERIOD_DAYS,
            'tip_address': settings.TIP_WALLET_ADDRESS,
            'platform_address': settings.PLATFORM_WALLET_ADDRESS
        }
    }
