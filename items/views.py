from django.shortcuts import render, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms import inlineformset_factory
from items.forms import CreateItemForm
from items.models import Item, ItemImage
from bids.models import ItemBid
from sales.models import ItemSale


def list_items(request):
    page_query = request.GET.get('page', 1)
    user_query = request.GET.get('user', 0)
    item_list = Item.objects.all().order_by('-list_date')

    # If the user query string resolves to real user, show their items, otherwise show all
    if user_query:
        user = User.objects.filter(id=user_query).first()
        if user:
            item_list = Item.objects.filter(owner=user).order_by('-list_date')

    paginator = Paginator(item_list, 20)

    try:
        items = paginator.page(page_query)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items
    }

    return render(request, 'items/list_items.html', context)

def get_item(request, item_id):
    item = Item.objects.get(id=item_id)
    item_images = item.images.all()
    item_bids = item.bids.all().order_by('-bid_price_xmr')
    sale = ItemSale.objects.filter(bid__in=item_bids, sale_cancelled=False).first()

    context = {
        'item': item,
        'item_images': item_images,
        'item_bids': item_bids,
        'sale': sale
    }

    return render(request, 'items/get_item.html', context)

@login_required
def create_item(request):
    ItemImageFormSet = inlineformset_factory(Item, ItemImage, fields=('image',))

    if request.method == 'POST':
        form = CreateItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.owner = request.user
            formset = ItemImageFormSet(request.POST, request.FILES, instance=new_item)
            if formset.is_valid():
                new_item.save()
                formset.save()
                return HttpResponseRedirect(reverse('get_item', args=[new_item.id]))
            else:
                messages.error(request, "Unable to save images.")
                for err in formset.errors:
                    messages.error(request, err)
                return HttpResponseRedirect(reverse('create_item'))
        else:
            form_errors = form.errors.get_json_data()
            for err in form_errors:
                err_data = form_errors[err][0]
                messages.error(request, f'{err}: {err_data["message"]}')
            return HttpResponseRedirect(reverse('create_item'))

    context = {
        'form': CreateItemForm(request.POST or None),
        'formset': ItemImageFormSet()
    }

    return render(request, 'items/create_item.html', context)

@login_required
def edit_item(request, item_id):
    item = Item.objects.get(id=item_id)
    ItemImageFormSet = inlineformset_factory(Item, ItemImage, fields=('image',))

    # Do not allow editing if current user is not the owner
    if request.user != item.owner:
        messages.error(request, "You can't edit an item you didn't post.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    # Do not allow editing if item is not available
    if item.available is False:
        messages.error(request, "You can't edit an item that is pending sale.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    if request.method == 'POST':
        form = CreateItemForm(request.POST, instance=item)
        if form.is_valid():
            saved_item = form.save(commit=False)
            formset = ItemImageFormSet(request.POST, request.FILES, instance=saved_item)
            if formset.is_valid():
                saved_item.save()
                formset.save()
                return HttpResponseRedirect(reverse('get_item', args=[item_id]))
            else:
                messages.error(request, "Unable to save images.")
                for err in formset.errors:
                    messages.error(request, err)
                return HttpResponseRedirect(reverse('get_item', args=[item_id]))
        else:
            form_errors = form.errors.get_json_data()
            for err in form_errors:
                err_data = form_errors[err][0]
                messages.error(request, f'{err}: {err_data["message"]}')
            return HttpResponseRedirect(reverse('get_item', args=[item_id]))
    else:
        context = {
            'form': CreateItemForm(instance=item),
            'formset': ItemImageFormSet(instance=item)
        }

        return render(request, 'items/edit_item.html', context)

@login_required
def delete_item(request, item_id):
    item = Item.objects.get(id=item_id)

    # Do not allow deleting if current user is not the owner
    if request.user != item.owner:
        messages.error(request, "You can't delete an item you didn't post.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    # Do not allow deleting if item is not available
    if item.available is False:
        messages.error(request, "You can't delete an item that is pending sale.")
        return HttpResponseRedirect(reverse('get_item', args=[item_id]))

    item.delete()
    messages.success(request, f"Item #{item_id}, \"{item.name}\", deleted!")
    return HttpResponseRedirect(reverse('list_items'))
