from django.db import models
from django.contrib.auth.models import User
from items.models import Item


class ItemBid(models.Model):
    item = models.ForeignKey(Item, related_name='bids', on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, related_name='bidder', on_delete=models.CASCADE)
    bid_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    bid_price_xmr = models.FloatField()
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.item.name} - {self.bidder} > {self.item.owner}"
