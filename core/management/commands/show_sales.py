import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.monero import AuctionWallet
from sales.models import ItemSale


class Command(BaseCommand):
    help = 'Shows mempool'

    def handle(self, *args, **kwargs):
        aw = AuctionWallet()
        if aw.connected is False:
            raise Exception('Unable to connect to auction wallet RPC endpoint.')

        msg = {'sales': []}
        item_sales = ItemSale.objects.all()
        for sale in item_sales:
            ew = aw.wallet.accounts[sale.escrow_account_index]
            msg['sales'].append({
                'account_index': sale.escrow_account_index,
                'sale_id': sale.id,
                'platform_paid': sale.platform_paid,
                'expected_payment_xmr': sale.expected_payment_xmr,
                'received_payment_xmr': sale.received_payment_xmr,
                'item_shipped': sale.item_shipped,
                'item_received': sale.item_received,
                'escrow_complete': sale.escrow_complete,
                'sale_finalized': sale.sale_finalized,
                'escrow_wallet_balances': {
                    'locked': float(ew.balances()[0]),
                    'unlocked': float(ew.balances()[1])
                }
            })

        self.stdout.write(json.dumps(msg))
