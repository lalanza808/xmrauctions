from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from monero.address import address
from core.monero import AuctionDaemon


def address_is_valid_monero(value):
    ad = AuctionDaemon()
    try:
        a = address(value)
        if ad.connected:
            net_type = ad.daemon.info()['nettype']
            if net_type == 'stagenet' and a.is_stagenet():
                return True
            elif net_type == 'testnet' and a.is_testnet():
                return True
            elif net_type == 'mainnet' and a.is_mainnet():
                return True
            else:
                raise ValidationError(
                    _('%(value)s is not a valid %(net_type)s address'),
                    params={
                        'value': value,
                        'net_type': net_type
                    }
                )
        return True
    except ValueError:
        raise ValidationError(
            _('%(value)s is an invalid Monero address'),
            params={'value': value},
        )
