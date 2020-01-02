from django import forms
from items.models import Item, address_is_valid_monero


class CreateItemForm(forms.ModelForm):
    payout_address = forms.CharField(validators=[address_is_valid_monero])

    class Meta:
        model = Item
        fields = ['name', 'description', 'ask_price_xmr', 'payout_address']
        labels = {
            'ask_price_xmr': 'Asking Price (XMR)',
            'payout_address': 'Payout Wallet Address'
        }
        help_texts = {
            'payout_address': 'Monero address where funds will be sent after sale is confirmed'
        }
