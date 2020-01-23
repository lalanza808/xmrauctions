import logging
from decimal import Decimal
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.conf import settings
from core.monero import AuctionWallet
from sales.models import ItemSale


logger = logging.getLogger('django.server')

@periodic_task(crontab(minute='*/3'))
def poll_for_buyer_escrow_payments():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('[ERROR] Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(payment_received=False)
    for sale in item_sales:
        logger.info(f'[INFO] Polling escrow address #{sale.escrow_account_index} for sale #{sale.id} for new funds.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
        unlocked = sale_account.balances()[1]
        sale.received_payment_xmr = unlocked
        if unlocked >= Decimal(str(sale.expected_payment_xmr)):
            logger.info(f'[INFO] Found payment of {sale.received_payment_xmr} XMR for sale #{sale.id}.')
            sale.payment_received = True

        sale.save()

@periodic_task(crontab(minute='*/3'))
def pay_sellers_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('[ERROR] Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(item_received=True, payment_received=True).filter(seller_paid=False)
    for sale in item_sales:
        # Take platform fees from the sale - the 50:50 split between buyer/seller
        sale_total = sale.agreed_price_xmr - sale.platform_fee_xmr
        sale_account = aw.wallet.accounts[sale.escrow_account_index]

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

        if sale.seller_paid and sale.seller_notified_of_payout is False:
            email_template = EmailTemplate(
                item=sale,
                scenario='sale_completed',
                role='seller'
            )
            sent = email_template.send()
            sale.seller_notified_of_payout = True
            sale.save()

@periodic_task(crontab(minute='*/30'))
def pay_platform_on_sold_items():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('[ERROR] Auction wallet is not connected. Quitting.')
        return False

    aof = settings.PLATFORM_WALLET_ADDRESS
    if aof is None:
        aof = str(aw.wallet.accounts[0].address())

    item_sales = ItemSale.objects.filter(escrow_complete=True, seller_paid=True, item_received=True).filter(platform_paid=False)
    for sale in item_sales:
        logger.info(f'[INFO] Paying platform fees for sale #{sale.id} to wallet {aof}.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
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

@periodic_task(crontab(minute='*'))
def closed_cancelled_sales():
    aw = AuctionWallet()
    if aw.connected is False:
        logging.error('[ERROR] Auction wallet is not connected. Quitting.')
        return False

    item_sales = ItemSale.objects.filter(sale_cancelled=True)
    for sale in item_sales:
        logger.info(f'[INFO] Deleting sale #{sale.id} and transferring back any sent funds to the buyer.')
        sale_account = aw.wallet.accounts[sale.escrow_account_index]
        if sale_account.balances()[0] > Decimal(0.0):
            try:
                sale_account.sweep_all(sale.bid.return_address)
                sale.delete()
            except Exception as e:
                logger.error(f'[ERROR] Unable to return funds to use for sale #{sale.id}.')
        else:
            sale.delete()
