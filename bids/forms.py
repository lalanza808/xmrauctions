from django import forms
from bids.models import ItemBid


class CreateItemBidForm(forms.ModelForm):
    class Meta:
        model = ItemBid
        fields = ['bid_price_xmr', 'return_address']
        labels = {
            'bid_price_xmr': 'Bid Price (XMR)',
            'return_address': 'Return Wallet Address'
        }
