from io import BytesIO
from base64 import b64encode
from qrcode import make as qrcode_make
from django.shortcuts import render, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import UserShippingAddress
from bids.models import ItemBid
from sales.models import ItemSale


@login_required
def get_sale(request, sale_id):
    sale = ItemSale.objects.get(id=sale_id)
    bid = ItemBid.objects.get(id=sale.bid.id)
    qr_uri = 'monero:{}?tx_amount={}&tx_description="xmrauctions_sale_{}"'.format(
        sale.escrow_address, sale.expected_payment_xmr, sale.id
    )

    # Do not proceed unless current user is a buyer or seller
    if request.user != bid.bidder and request.user != sale.item.owner:
        messages.error(request, "You can't view a sale you are not involved in.")
        return HttpResponseRedirect(reverse('home'))

    # Do not proceed if sale is cancelled
    if sale.sale_cancelled:
        messages.error(request, 'That sale has been cancelled and is no longer available.')
        return HttpResponseRedirect(reverse('get_item', args=[sale.item.id]))

    _address_qr = BytesIO()
    address_qr = qrcode_make(qr_uri).save(_address_qr)

    context = {
        'sale': sale,
        'qrcode': b64encode(_address_qr.getvalue()).decode(),
        'shipping_address': UserShippingAddress.objects.filter(
            user=bid.bidder
        ).first()
    }

    return render(request, 'sales/get_sale.html', context)

@login_required
def cancel_sale(request, sale_id):
    sale = ItemSale.objects.filter(id=sale_id).first()
    bid = ItemBid.objects.get(id=sale.bid.id)

    if sale is None:
        messages.error(request, "That sale doesn't exist.")
        return HttpResponseRedirect(reverse('home'))

    # Do not proceed unless current user is a buyer or seller
    if request.user != sale.bid.bidder and request.user != sale.item.owner:
        messages.error(request, "You can't view a sale you are not involved in.")
        return HttpResponseRedirect(reverse('home'))

    if sale.payment_received:
        messages.error(request, "You can't cancel a sale which has already received funds.")
        return HttpResponseRedirect(reverse('get_sale', args=[sale.id]))

    # Item becomes available
    sale.item.available = True
    sale.item.save()

    # Bid becomes not accepted
    sale.bid.accepted = False
    sale.bid.save()

    # Sale gets cancelled
    sale.sale_cancelled = True
    sale.save()
    return HttpResponseRedirect(reverse('get_item', args=[sale.item.id]))


@login_required
def confirm_shipment(request, sale_id):
    sale = ItemSale.objects.get(id=sale_id)

    # TODO - dont allow shipment if we dont have an address

    # Only proceed if current user is the seller
    if request.user == sale.item.owner:
        sale.item_shipped = True
        sale.save()
        messages.success(request, "Package sent, buyer notified!")
        return HttpResponseRedirect(reverse('get_sale', args=[sale.id]))
    else:
        messages.error(request, "You can't confirm a package shipment for an item you don't own.")
        return HttpResponseRedirect(reverse('home'))

@login_required
def confirm_receipt(request, sale_id):
    sale = ItemSale.objects.get(id=sale_id)

    # Do not proceed unless current user is the buyer
    if request.user == sale.bid.bidder:
        sale.item_received = True
        sale.save()
        messages.success(request, "Item received!")
        return HttpResponseRedirect(reverse('get_sale', args=[sale.id]))
    else:
        messages.error(request, "You can't confirm receipt of an item you didn't purchase.")
        return HttpResponseRedirect(reverse('home'))
