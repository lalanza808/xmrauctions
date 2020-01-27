from secrets import token_urlsafe
from monero.seed import Seed
from django.test import TestCase
from django.contrib.auth.models import User
from bids.models import ItemBid
from items.models import Item


class ItemBidModelsTestCase(TestCase):
    def setUp(self):
        self.seller_password = token_urlsafe(32)
        self.buyer_password = token_urlsafe(32)

        self.seller = User.objects.create_user(
            'seller', self.seller_password
        )
        self.buyer = User.objects.create_user(
            'buyer', self.buyer_password
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

    def test_create_itembid(self):
        test_itembid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        obj_name = f'{test_itembid.id} - {test_itembid.item.name} - {test_itembid.bidder} > {test_itembid.item.owner}'
        self.assertTrue(isinstance(test_itembid, ItemBid))
        self.assertEqual(test_itembid.__str__(), obj_name)