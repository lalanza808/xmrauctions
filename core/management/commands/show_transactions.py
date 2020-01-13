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

        msg = {'balances': []}
        if kwargs.get('all', False):
            for index,account in enumerate(aw.wallet.accounts):
                msg['balances'].append({
                    "index": index,
                    "address": str(account.address()),
                    "locked_balance": float(account.balances()[0]),
                    "unlocked_balance": float(account.balances()[1]),
                    "outgoing": [str(i) for i in account.outgoing()],
                    "incoming": [str(i) for i in account.incoming()],
                })
        else:
            item_sales = ItemSale.objects.all()
            for sale in item_sales:
                w = aw.wallet.accounts[sale.escrow_account_index]
                msg['balances'].append({
                    "sale_id": sale.id,
                    "address": str(w.address()),
                    "locked_balance": float(w.balances()[0]),
                    "unlocked_balance": float(w.balances()[1]),
                    "outgoing": [str(i) for i in w.outgoing()],
                    "incoming": [str(i) for i in w.incoming()],
                })

        self.stdout.write(json.dumps(msg))
