import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.monero import AuctionDaemon
from sales.models import ItemSale


class Command(BaseCommand):
    help = 'Shows mempool'

    def handle(self, *args, **kwargs):
        ad = AuctionDaemon()
        if ad.connected is False:
            raise Exception('Unable to connect to auction daemon RPC endpoint.')

        msg = str(ad.daemon.mempool())
        self.stdout.write(self.style.SUCCESS(msg))
