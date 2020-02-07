from django_prometheus.models import ExportModelOperationsMixin
from django.db import models
from django.contrib.auth.models import User
from items.models import Item
from core.validators import address_is_valid_monero


class ItemBid(ExportModelOperationsMixin('item_bid'), models.Model):
    item = models.ForeignKey(Item, related_name='bids', on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, related_name='bidder', on_delete=models.CASCADE)
    bid_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    bid_price_xmr = models.FloatField()
    accepted = models.BooleanField(default=False)
    return_address = models.CharField(max_length=100, validators=[address_is_valid_monero])

    def __str__(self):
        return f"{self.id} - {self.item.name} - {self.bidder} > {self.item.owner}"
