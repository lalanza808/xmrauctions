from django import template
from django.conf import settings


register = template.Library()

@register.filter(is_safe=True)
def search_block_explorer(param):
    search_url = f'{settings.BLOCK_EXPLORER}search?value={param}'
    return search_url
