from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from monero.address import address


def address_is_valid_monero(value):
    try:
        address(value)
        return True
    except ValueError:
        raise ValidationError(
            _('%(value)s is an invalid Monero address'),
            params={'value': value},
        )
