from django import forms
from core.models import UserShippingAddress


class UserShippingAddressForm(forms.ModelForm):
    class Meta:
        model = UserShippingAddress
        fields = [
            'address1',
            'address2',
            'city',
            'state',
            'country',
            'zip'
        ]

        labels = {
            'address1': 'Address',
            'address2': 'Address (additional info)'
        }
