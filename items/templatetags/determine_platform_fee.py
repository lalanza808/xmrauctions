from math import ceil
from django import template
from django.conf import settings


register = template.Library()

@register.filter(is_safe=True)
def determine_platform_fee(value):
    platform_fee_xmr = float(value * (settings.PLATFORM_FEE_PERCENT / 100) / 2)
    return round(platform_fee_xmr, 4)
