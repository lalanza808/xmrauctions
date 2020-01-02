from django.shortcuts import HttpResponseRedirect, reverse
from core.models import UserShippingAddress


class EnforceShippingAddressCreationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # If current user is authenticated, get their shipping information and current page
        # If current page is not them editing their address or logging out, redirect them
        if request.user.is_authenticated:
            profile = UserShippingAddress.objects.filter(user=request.user).first()
            is_profile_absent = profile is None

            allowed_paths = [
                reverse('edit_shipping'),
                reverse('logout')
            ]
            on_allowed_path = request.path not in allowed_paths

            if is_profile_absent and on_allowed_path:
                return HttpResponseRedirect(reverse('edit_shipping'))

        response = self.get_response(request)

        return response
