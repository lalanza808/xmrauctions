from django.shortcuts import render, HttpResponseRedirect, reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.conf import settings
from core.forms import UserShippingAddressForm
from core.models import UserShippingAddress
from core.monero import AuctionDaemon, AuctionWallet


def home(request):
    daemon_info = cache.get('daemon_info', None)
    monero_info = cache.get('monero_info', None)

    if daemon_info is None:
        d = AuctionDaemon()
        if d.connected:
            daemon_info = d.daemon.info()

    context = {
        'daemon_info': daemon_info,
        'monero_info': monero_info
    }

    return render(request, 'home.html', context)

def health(request):
    daemon = AuctionDaemon()
    wallet = AuctionWallet()

    context = {
        'daemon_connected': daemon.connected,
        'wallet_connected': wallet.connected
    }

    return JsonResponse(context)

def devops_dashboard(request):
    dodb = settings.DEVOPS_DASHBOARD
    if dodb:
        return HttpResponseRedirect(dodb)
    else:
        return HttpResponseRedirect(reverse('health'))

def get_help(request):
    return render(request, 'core/help.html')

@login_required
def edit_shipping(request):
    profile = UserShippingAddress.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = UserShippingAddressForm(request.POST, instance=profile)
        if form.is_valid():
            saved_profile = form.save(commit=False)
            saved_profile.user = request.user
            saved_profile.save()
            messages.success(request, 'Profile updated.')
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, 'Unable to save shipping information.')
            form_errors = form.errors.get_json_data()
            for err in form_errors:
                err_data = form_errors[err][0]
                messages.error(request, f'{err}: {err_data["message"]}')

    context = {
        'form': UserShippingAddressForm(instance=profile)
    }

    return render(request, 'core/edit_shipping.html', context)
