from django import template
from django.conf import settings
from core.monero import connect_rpc


register = template.Library()

@register.filter(is_safe=True)
def search_block_explorer(param):
    daemon_rpc = connect_rpc('daemon')
    if daemon_rpc:
        net_type = daemon_rpc.daemon.info()['nettype']
        explorer_url = settings.BLOCK_EXPLORER % net_type
        search_url = f'{explorer_url}/tx/{param}/autorefresh'
        return search_url
    else:
        return '#'
