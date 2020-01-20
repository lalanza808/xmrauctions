from requests import get as r_get
from logging import getLogger
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.core.cache import cache
from django.conf import settings
from core.monero import AuctionDaemon, AuctionWallet


logger = getLogger('django.server')

@periodic_task(crontab(minute='*/8'))
def retrieve_daemon_stats():
    logger.info('[INFO] Retrieving daemon statistics')
    ad = AuctionDaemon()
    if ad.connected:
        daemon_info = ad.daemon.info()
        cache.set('daemon_info', daemon_info, settings.CACHE_TTL)

@periodic_task(crontab(minute='*/20'))
def retrieve_monero_stats():
    logger.info('[INFO] Retrieve Monero market statistics from Coin Gecko')
    data = {
        'localization': False,
        'tickers': False,
        'market_data': True,
        'community_data': False,
        'developer_data': False,
        'sparkline': False
    }
    headers = {
        'accept': 'application/json'
    }
    r = r_get('https://api.coingecko.com/api/v3/coins/monero', headers=headers, data=data)
    monero_info = {
        'genesis_date': r.json()['genesis_date'],
        'market_cap_rank': r.json()['market_cap_rank'],
        'current_price': r.json()['market_data']['current_price']['usd'],
        'market_cap': r.json()['market_data']['market_cap']['usd'],
        'market_cap_rank': r.json()['market_data']['market_cap_rank'],
        'total_volume': r.json()['market_data']['total_volume']['usd'],
        'last_updated': r.json()['last_updated']
    }
    logger.info(monero_info)
    cache.set('monero_info', monero_info, settings.CACHE_TTL)
