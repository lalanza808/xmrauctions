from django import forms
from items.models import Item, address_is_valid_monero


class CreateItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['sale_type', 'name', 'description', 'whereabouts', 'ask_price_xmr', 'payout_address']
        labels = {
            'ask_price_xmr': 'Asking Price (XMR)',
            'payout_address': 'Payout Wallet Address',
            'sale_type': 'Method of Delivery'
        }
        help_texts = {
            'name': 'Use a succinct name for your item. Don\'t be spammy or obscene.',
            'description': 'Describe the condition of the item and any important information. Try to refrain from sharing personally identifiable information like phone numbers or social media links.',
            'whereabouts': 'If shipping, use your general location like a nearby capital city and your state. If meeting, use the meetup location with street address.',
            'ask_price_xmr': 'How many moneroj do you want for your item?',
            'payout_address': 'A Monero wallet address where funds will be sent after sale is confirmed.',
        }

class SearchItemForm(forms.Form):
    search = forms.CharField(
        label='',
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder':'Search whereabouts, item name, or description'}
        )
    )
