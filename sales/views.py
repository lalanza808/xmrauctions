from io import BytesIO
from base64 import b64encode
from qrcode import make as qrcode_make
from django.shortcuts import render, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bids.models import ItemBid
from sales.models import ItemSale



@login_required
def get_sale(request, bid_id):
    bid = ItemBid.objects.get(id=bid_id)
    sale = ItemSale.objects.get(bid=bid)

    # Do not proceed unless current user is a buyer or seller
    if request.user != bid.bidder and request.user != sale.item.owner:
        messages.error(request, "You can't view a sale you are not involved in.")
        return HttpResponseRedirect(reverse('home'))

    _address_qr = BytesIO()
    address_qr = qrcode_make(sale.escrow_address).save(_address_qr)

    context = {
        'sale': sale,
        'qrcode': b64encode(_address_qr.getvalue()).decode()
    }

    return render(request, 'sales/get_sale.html', context)
