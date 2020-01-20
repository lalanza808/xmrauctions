from logging import getLogger
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.core.cache import cache
from django.conf import settings
from core.monero import AuctionDaemon, AuctionWallet


logger = getLogger('django.server')

@periodic_task(crontab(minute='*'))
def retrieve_daemon_stats():
    logger.info('[INFO] Retrieving daemon statistics')
    ad = AuctionDaemon()
    if ad.connected:
        daemon_info = ad.daemon.info()
        cache.set('daemon_info', daemon_info, settings.CACHE_TTL)
