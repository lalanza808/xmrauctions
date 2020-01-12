from django.shortcuts import render, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bids.forms import CreateItemBidForm
from bids.models import ItemBid
from sales.models import ItemSale
from items.models import Item
from core.monero import AuctionWallet


@login_required
def list_bids(request):
    page_query = request.GET.get('page', 1)
    bid_list = ItemBid.objects.filter(bidder=request.user)
    sales = ItemSale.objects.filter(bid__in=bid_list)
    paginator = Paginator(bid_list, 20)

    try:
      bids = paginator.page(page_query)
    except PageNotAnInteger:
      bids = paginator.page(1)
    except EmptyPage:
      bids = paginator.page(paginator.num_pages)

    context = {
        'bids': bids,
        'sales': sales
    }

    return render(request, 'bids/list_bids.html', context)

@login_required
def create_bid(request, item_id):
    item = Item.objects.get(id=item_id)
    current_user_bid = item.bids.filter(bidder=request.user).first()

    # Do not allow bidding if current user is the owner
    if request.user == item.owner:
        messages.error(request, "You can't bid on an item you posted.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    # Do not allow bidding if item is not available
    if item.available is False:
        messages.error(request, "You can't bid on an item pending sale.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    # Redirect user to edit their existing bid if one exists
    if current_user_bid:
        return HttpResponseRedirect(reverse('edit_bid', args=[current_user_bid.id]))

    if request.method == 'POST':
        form = CreateItemBidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.bidder = request.user
            bid.item = item
            bid.save()
            return HttpResponseRedirect(reverse('get_item', args=[item_id]))
        else:
            form_errors = form.errors.get_json_data()
            for err in form_errors:
                err_data = form_errors[err][0]
                messages.error(request, f'{err}: {err_data["message"]}')
            return HttpResponseRedirect(reverse('create_bid', args=[item_id]))
    else:
        context = {
            'form': CreateItemBidForm(),
            'item': item
        }

        return render(request, 'bids/create_bid.html', context)


@login_required
def edit_bid(request, bid_id):
    bid = ItemBid.objects.get(id=bid_id)

    # Do not allow editing if current user doesn't own the bid
    if request.user != bid.bidder:
        messages.error(request, "You can't edit a bid that doesn't belong to you.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not allow editing if bid is accepted already
    if bid.accepted:
        messages.error(request, "You can't edit a bid that has already been accepted.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    if request.method == 'POST':
        form = CreateItemBidForm(request.POST, instance=bid)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))
        else:
            form_errors = form.errors.get_json_data()
            for err in form_errors:
                err_data = form_errors[err][0]
                messages.error(request, f'{err}: {err_data["message"]}')
            return HttpResponseRedirect(reverse('create_bid', args=[bid.item.id]))
    else:
        context = {
            'form': CreateItemBidForm(instance=bid),
            'bid': bid
        }

        return render(request, 'bids/edit_bid.html', context)

@login_required
def accept_bid(request, bid_id):
    aw = AuctionWallet()
    bid = ItemBid.objects.filter(id=bid_id).first()
    platform_fee_xmr = bid.bid_price_xmr * (settings.PLATFORM_FEE_PERCENT / 100) / 2 # split buyer/seller
    expected_payment_xmr = bid.bid_price_xmr + platform_fee_xmr
    account_label = f'Sale account for Item #{bid.item.id}, Bid #{bid.id}'

    # Do not allow accepting your own bid
    if request.user == bid.bidder:
        messages.error(request, "You can't accept your own bid.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not allow accepting the bid unless you own the item that received the bid
    if request.user != bid.item.owner:
        messages.error(request, "You can't accept a bid if you don't own the item.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not proceed if item is not available
    if bid.item.available is False:
        messages.error(request, "You can't accept the bid because the item is pending sale.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not proceed if bid is already accepted
    if bid.accepted:
        messages.error(request, "You can't accept a bid if it has already been accepted.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not proceed if there platform wallet is not connected
    if aw.connected is False:
        messages.error(request, "You can't accept the bid because the platform wallet is not properly connected.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Item becomes unavailable
    bid.item.available = False
    bid.item.save()

    # Bid becomes accepted
    bid.accepted = True
    bid.save()

    # Generate new Monero account for the sale
    new_account = aw.wallet.new_account(label=account_label)

    # Sale is created
    sale = ItemSale(
        item=bid.item,
        bid=bid,
        escrow_address=new_account.address(),
        escrow_account_index=new_account.index,
        agreed_price_xmr=bid.bid_price_xmr,
        platform_fee_xmr=platform_fee_xmr,
        expected_payment_xmr=expected_payment_xmr
    )
    sale.save()

    return HttpResponseRedirect(reverse('get_sale', args=[sale.id]))

@login_required
def delete_bid(request, bid_id):
    bid = ItemBid.objects.get(id=bid_id)

    # Do not allow deleting the bid unless you own the bid
    if request.user != bid.bidder:
        messages.error(request, "You can't delete a bid you did not create.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    # Do not allow deleting if the bid is accepted
    if bid.accepted:
        messages.error(request, "You can't delete a bid if it has been accepted.")
        return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))

    bid.delete()
    messages.success(request, f"Bid #{bid_id} on item \"{bid.item.name}\" ({bid.item.id}) has been deleted.")
    return HttpResponseRedirect(reverse('get_item', args=[bid.item.id]))
