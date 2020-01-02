from django.conf import settings


def inject_site_meta(request):
    return {
        'site_meta': {
            'debug': settings.DEBUG,
            'name': settings.SITE_NAME
        }
    }
