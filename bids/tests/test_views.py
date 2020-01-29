from secrets import token_urlsafe
from monero.seed import Seed
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.paginator import Page
from django.shortcuts import reverse
from django.test.client import Client
from items.models import Item
from bids.models import ItemBid
from bids.views import list_bids


class ItemBidModelsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller_password = token_urlsafe(32)
        self.buyer_password = token_urlsafe(32)

        self.seller = User.objects.create_user(
            'seller', password=self.seller_password
        )
        self.buyer = User.objects.create_user(
            'buyer', password=self.buyer_password
        )
        self.payout_address = Seed().public_address()
        self.return_address = Seed().public_address()
        self.whereabouts = 'Los Angeles, CA'

        self.test_item = Item.objects.create(
            owner=self.seller,
            name='Test Item',
            description='Test item',
            ask_price_xmr=0.3,
            payout_address=self.payout_address,
            whereabouts=self.whereabouts
        )

    def test_list_bids_requires_auth(self):
        response = self.client.get(reverse('list_bids'))
        request = response.wsgi_request
        response = list_bids(request)
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(response.status_code, 302)


    def test_list_bids_returns_pagination(self):
        ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username='buyer', password=self.buyer_password)
        response = self.client.get(reverse('list_bids'))
        response_w_str_arg = self.client.get(reverse('list_bids') + "?page=bar")
        response_w_empty_pg = self.client.get(reverse('list_bids') + "?page=9001")
        self.client.logout()
        self.assertTrue(isinstance(response.context['bids'], Page), 'Paginated object not returned')
        self.assertTrue(isinstance(response_w_str_arg.context['bids'], Page), 'Paginated object not returned')
        self.assertTrue(isinstance(response_w_empty_pg.context['bids'], Page), 'Paginated object not returned')

    def test_list_bids_returns_only_user_bids(self):
        pass
