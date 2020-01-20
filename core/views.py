from django.shortcuts import render, HttpResponseRedirect, reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from core.forms import UserShippingAddressForm
from core.models import UserShippingAddress
from core.monero import AuctionDaemon, AuctionWallet


def home(request):
    daemon_info = cache.get('daemon_info', None)

    if daemon_info is None:
        d = AuctionDaemon()
        if d.connected:
            daemon_info = AuctionDaemon().daemon.info()
        else:
            daemon_info = False

    return render(request, 'home.html', {'daemon_info': daemon_info})

def health(request):
    daemon = AuctionDaemon()
    wallet = AuctionWallet()

    context = {
        'daemon_connected': daemon.connected,
        'wallet_connected': wallet.connected
    }

    return JsonResponse(context)

def get_faqs(request):
    return render(request, 'core/faqs.html')

def get_privacy(request):
    return render(request, 'core/privacy.html')

def get_terms(request):
    return render(request, 'core/terms.html')


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
