import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.monero import AuctionWallet
from sales.models import ItemSale


class Command(BaseCommand):
    help = 'Shows balances of all sale items'

    def add_arguments(self, parser):
        parser.add_argument('-a', '--all', action='store_true', help='Whether or not to scan whole wallet vs item sales', default=False)

    def handle(self, *args, **kwargs):
        aw = AuctionWallet()
        if aw.connected is False:
            raise Exception('Unable to connect to auction wallet RPC endpoint.')

        msg = []

        if kwargs.get('all', False):
            self.stdout.write(self.style.SUCCESS(len(aw.wallet.accounts)))
            for index,account in enumerate(aw.wallet.accounts):
                msg.append({
                    "index": index,
                    "address": str(account.address()),
                    "locked_balance": str(account.balances()[0]),
                    "unlocked_balance": str(account.balances()[1]),
                    "outgoing": account.outgoing(),
                    "incoming": account.incoming(),
                })
        else:
            item_sales = ItemSale.objects.all()
            for sale in item_sales:
                w = aw.wallet.accounts[sale.escrow_account_index]
                msg.append({
                    "sale_id": sale.id,
                    "address": str(w.address()),
                    "locked_balance": str(w.balances()[0]),
                    "unlocked_balance": str(w.balances()[1]),
                    "outgoing": w.outgoing(),
                    "incoming": w.incoming(),
                })

        for i in msg:
            self.stdout.write(self.style.SUCCESS(i))
