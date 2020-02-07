from django_prometheus.models import ExportModelOperationsMixin
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from items.models import Item
from bids.models import ItemBid


class ItemSale(ExportModelOperationsMixin('item_sale'), models.Model):
    item = models.ForeignKey(Item, related_name='sales', on_delete=models.CASCADE)
    bid = models.ForeignKey(ItemBid, related_name='bids', on_delete=models.CASCADE)
    escrow_address = models.CharField(max_length=96)
    escrow_account_index = models.IntegerField()
    agreed_price_xmr = models.FloatField()
    platform_fee_xmr = models.FloatField()
    network_fee_xmr = models.FloatField(default=0.0)
    seller_payout_transaction = models.CharField(max_length=150, blank=True)
    expected_payment_xmr = models.FloatField()
    received_payment_xmr = models.FloatField(default=0.0)
    escrow_period_days = models.PositiveSmallIntegerField(default=settings.ESCROW_PERIOD_DAYS)
    buyer_notified = models.BooleanField(default=False)
    buyer_notified_of_shipment = models.BooleanField(default=False)
    payment_received = models.BooleanField(default=False)
    seller_notified = models.BooleanField(default=False)
    seller_notified_of_receipt = models.BooleanField(default=False)
    payment_refunded = models.BooleanField(default=False)
    item_shipped = models.BooleanField(default=False)
    item_received = models.BooleanField(default=False)
    buyer_disputed = models.BooleanField(default=False)
    seller_disputed = models.BooleanField(default=False)
    escrow_complete = models.BooleanField(default=False)
    seller_paid = models.BooleanField(default=False)
    seller_notified_of_payout = models.BooleanField(default=False)
    platform_paid = models.BooleanField(default=False)
    sale_finalized = models.BooleanField(default=False)
    sale_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.item.name} - {self.bid.bidder} > {self.item.owner}"
