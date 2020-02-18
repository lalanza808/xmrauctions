from secrets import token_urlsafe
from monero.seed import Seed
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.shortcuts import reverse
from bids.models import ItemBid
from items.models import Item
from core.helpers.email_template import EmailTemplate
from sales.models import ItemSale


class ItemBidModelsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller_password = token_urlsafe(32)
        self.buyer_password = token_urlsafe(32)

        self.seller = User.objects.create_user(
            'seller', self.seller_password
        )
        self.buyer = User.objects.create_user(
            'buyer', self.buyer_password
        )
        self.payout_address = Seed().public_address(net='stagenet')
        self.return_address = Seed().public_address(net='stagenet')
        self.whereabouts = 'Los Angeles, CA'

        self.test_item = Item.objects.create(
            owner=self.seller,
            name='Test Item',
            description='Test item',
            ask_price_xmr=0.3,
            payout_address=self.payout_address,
            whereabouts=self.whereabouts
        )


    def test_email_template_helper_sends_successfully_for_(self):
        e = EmailTemplate(
            item=self.test_item,
            scenario='item_has_bids',
            role='seller'
        )
        res = e.send()
        self.assertEqual(res, 1)

    def test_email_template_helper_sends_successfully_for_aaa(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('accept_bid', args=[new_bid.id]))
        item_sale = ItemSale.objects.filter(item=self.test_item, bid=new_bid).first()
        updated_bid = ItemBid.objects.get(id=new_bid.id)
        self.assertTrue(updated_bid.accepted)
        self.assertFalse(updated_bid.item.available)

        e = EmailTemplate(
            item=item_sale,
            scenario='item_shipped',
            role='buyer'
        )
        res = e.send()
        self.assertEqual(res, 1)
