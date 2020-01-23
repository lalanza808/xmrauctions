import logging
from decimal import Decimal
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.conf import settings
from django.core.cache import cache
from core.monero import connect_rpc
from sales.models import ItemSale


logger = logging.getLogger('django.server')

@periodic_task(crontab(minute='*/2'))
def poll_for_buyer_escrow_payments():
    wallet_rpc = connect_rpc("wallet")
    item_sales = ItemSale.objects.filter(payment_received=False)
    for sale in item_sales:
        logger.info(f'[INFO] Polling escrow address #{sale.escrow_account_index} for sale #{sale.id} for new funds.')
        sale_account = wallet_rpc.wallet.accounts[sale.escrow_account_index]
        tx_in = sale_account.incoming()
        balances = sale_account.balances()
        sale.received_payment_xmr = balances[0]
        if balances[0] >= Decimal(str(sale.expected_payment_xmr)) and tx_in:
            logger.info(f'[INFO] Found incoming transaction {tx_in[0].transaction} of {sale.received_payment_xmr} XMR for sale #{sale.id}.')
            if tx_in[0].transaction.confirmations >= settings.BLOCK_CONFIRMATIONS_RCV:
                logger.info(f'[INFO] The incoming transaction has {settings.BLOCK_CONFIRMATIONS_RCV} confirmations and enough funds. Marking payment received.')
                sale.payment_received = True
            else:
                logger.info(f'[INFO] The incoming transaction only has {tx_in[0].transaction.confirmations} confirmations. Not enough to proceed.')

        sale.save()

@periodic_task(crontab(minute='*/4'))
def pay_sellers_on_sold_items():
    wallet_rpc = connect_rpc("wallet")
    item_sales = ItemSale.objects.filter(item_received=True, payment_received=True).filter(seller_paid=False)
    for sale in item_sales:
        # Take platform fees from the sale - the 50:50 split between buyer/seller
        sale_total = sale.agreed_price_xmr - sale.platform_fee_xmr
        sale_account = wallet_rpc.wallet.accounts[sale.escrow_account_index]
        logger.info(f'[INFO] Seller needs to be paid for sale #{sale.id}. Found balances of {sale_account.balances()} in account #{sale.escrow_account_index}.')
        if sale_account.balances()[1] >= Decimal(str(sale.agreed_price_xmr)):
            try:
                # Construct a transaction so we can get current fee and subtract from the total
                _tx = sale_account.transfer(
                    sale.item.payout_address, Decimal(.01), relay=False
                )
                new_total = sale_total - float(_tx[0].fee)
                logger.info(f'[INFO] Sending {new_total} XMR from wallet account #{sale.escrow_account_index} to item owner\'s payout address for sale #{sale.id}.')
                # Make the transaction with network fee removed
                tx = sale_account.transfer(
                    sale.item.payout_address, new_total, relay=True
                )
                sale.network_fee_xmr = _tx[0].fee
                sale.seller_payout_transaction = tx[0]
                sale.seller_paid = True
                sale.escrow_complete = True
                sale.save()
            except Exception as e:
                logger.error(f'[ERROR] Unable to pay seller for sale #{sale.id}: ')
        else:
            logger.warning(f'[WARNING] Not enough unlocked funds available in account #{sale.escrow_account_index} for sale #{sale.id}.')

@periodic_task(crontab(minute='*/30'))
def pay_platform_on_sold_items():
    wallet_rpc = connect_rpc("wallet")
    aof = settings.PLATFORM_WALLET_ADDRESS
    if aof is None:
        aof = str(wallet_rpc.wallet.accounts[0].address())

    item_sales = ItemSale.objects.filter(escrow_complete=True, seller_paid=True, item_received=True).filter(platform_paid=False)
    for sale in item_sales:
        logger.info(f'[INFO] Paying platform fees for sale #{sale.id} to wallet {aof}.')
        sale_account = wallet_rpc.wallet.accounts[sale.escrow_account_index]
        bal = sale_account.balances()[1]
        if bal >= 0:
            try:
                if settings.PLATFORM_FEE_PERCENT > 0:
                    logger.info(f'[INFO] Getting platform fees of {bal} XMR')
                    sale_account.sweep_all(aof)
                else:
                    logging.info('No platform fees are set - proceeding without taking fees.')

                sale.platform_paid = True
                sale.sale_finalized = True
                sale.save()
                return True
            except Exception as e:
                logger.error(f'[ERROR] Unable to pay platform for sale #{sale.id} - trying again')
        else:
            logger.warning(f'[WARNING] Not enough unlocked funds available in account #{sale.escrow_account_index} for sale #{sale.id}.')

@periodic_task(crontab(minute='*/4'))
def refund_buyers_on_cancelled_sales() -> bool:
    """
    Issue a refund to the buyer if they sent money but then cancelled the sale.

    :rtype: bool
    """
    wallet_rpc = connect_rpc("wallet")
    item_sales = ItemSale.objects.filter(sale_cancelled=True, payment_refunded=False)
    for sale in item_sales:
        logger.info(f'[INFO] Refunding any sent funds from the buyer for sale #{sale.id}.')
        sale_total = sale.agreed_price_xmr - sale.platform_fee_xmr
        sale_account = wallet_rpc.wallet.accounts[sale.escrow_account_index]
        balances = sale_account.balances()
        logger.info(f'[INFO] Found balances of {balances} XMR for sale #{sale.id}.')
        if balances[0] != balances[1]:
            logger.info(f'[INFO] Balances not yet equal. Waiting')
            return False
        elif balances[1] > Decimal(0.0):
            try:
                # Construct a transaction so we can get current fee and subtract from the total
                _tx = sale_account.transfer(
                    sale.bid.return_address, Decimal(.01), relay=False
                )
                new_total = sale_total - float(_tx[0].fee)
                logger.info('[INFO] Refunding {new_total} XMR from wallet account #{sale.escrow_account_index} to buyer\'s return address for sale #{sale.id}.')
                # Make the transaction with network fee removed
                tx = sale_account.transfer(
                    sale.bid.return_address, new_total, relay=True
                )
                if tx:
                    sale.payment_refunded = True
                    sale.save()
                    logger.info(f'[INFO] Balance returned to buyer for sale #{sale.id}.')
                    return True
                else:
                    return False
            except Exception as e:
                logger.error(f'[ERROR] Unable to return funds to use for sale #{sale.id}: {e}')
                return False
        else:
            if cache.get(f'{sale.id}_sale_refund_tries'):
                logger.info(f'[INFO] Balance for sale #{sale.id} is 0 still. Marking payment_refunded flag.')
                sale.payment_refunded = True
                sale.save()
                return True
            else:
                logger.info(f'[INFO] Setting flag in cache for sale #{sale.id} to try another block cycle for good measure.')
                cache.set(f'{sale.id}_sale_refund_tries', {"tries": 1}, settings.CACHE_TTL)
