from secrets import token_urlsafe
from monero.seed import Seed
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.paginator import Page
from django.shortcuts import reverse
from django.test.client import Client
from items.models import Item
from bids.models import ItemBid
from bids.forms import CreateItemBidForm
from sales.models import ItemSale


class ItemBidViewsTestCase(TestCase):
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

    ##### List Bids

    def test_list_bids_requires_auth(self):
        response = self.client.get(reverse('list_bids'))
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(response.status_code, 302)

    def test_list_bids_returns_pagination(self):
        ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('list_bids'))
        response_w_str_arg = self.client.get(reverse('list_bids') + "?page=bar")
        response_w_empty_pg = self.client.get(reverse('list_bids') + "?page=9001")
        self.client.logout()
        self.assertTrue(isinstance(response.context['bids'], Page), 'Paginated object not returned')
        self.assertTrue(isinstance(response_w_str_arg.context['bids'], Page), 'Paginated object not returned')
        self.assertTrue(isinstance(response_w_empty_pg.context['bids'], Page), 'Paginated object not returned')

    def test_list_bids_returns_only_user_bids(self):
        for i in range(1, 20):
            u = User.objects.create_user(f'list_bids_test{i}', password=token_urlsafe(16))
            ItemBid.objects.create(
                item=self.test_item,
                bidder=u,
                bid_price_xmr=0.2,
                return_address=self.return_address
            )

        ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )

        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('list_bids'))
        self.client.logout()

        # Test that buyer's bids are the only bids returned from view
        all_bids = ItemBid.objects.all()
        user_bids = all_bids.filter(bidder=self.buyer)
        self.assertEqual(len(user_bids), len(response.context['bids']))
        self.assertLess(len(user_bids), len(all_bids))

        # Test that each bid belongs to the buyer
        for bid in response.context['bids']:
            self.assertEqual(bid.bidder, self.buyer)

    ##### Create Bid

    def test_create_bid_requires_auth(self):
        response = self.client.get(reverse('create_bid', args=[self.test_item.id]))
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(response.status_code, 302)

    def test_create_bid_redirect_home_if_item_id_missing(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('create_bid', args=[9999]))
        self.client.logout()
        self.assertEqual(response.url, reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_create_bid_redirect_edit_if_bid_already_posted(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.2,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('create_bid', args=[self.test_item.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('edit_bid', args=[new_bid.id]))
        self.assertEqual(response.status_code, 302)
        new_bid.delete()

    def test_create_bid_redirect_item_if_user_owns_item(self):
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('create_bid', args=[self.test_item.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)

    def test_create_bid_redirect_item_if_item_unavailable(self):
        self.test_item.available = False
        self.test_item.save()
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('create_bid', args=[self.test_item.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)

    def test_create_bid_save_redirect_if_valid(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.post(reverse('create_bid', args=[self.test_item.id]), {
            'bid_price_xmr': 0.2,
            'return_address': self.return_address,
        })
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertTrue(buyer_bid)
        buyer_bid.delete()

    def test_create_bid_no_save_redirect_if_invalid(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.post(reverse('create_bid', args=[self.test_item.id]), {
            'bid_price_xmr': 'invalid bid price',
            'return_address': 'invalid return address',
        })
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('create_bid', args=[self.test_item.id]))
        self.assertIsNone(buyer_bid)

    def test_create_bid_returns_valid_context(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('create_bid', args=[self.test_item.id]))
        self.client.logout()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['item'].id, self.test_item.id)
        self.assertTrue(response.context['form'])
        self.assertIsInstance(response.context['form'], CreateItemBidForm)

    ##### Edit Bid

    def test_edit_bid_requires_auth(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.2,
            return_address=self.return_address
        )
        response = self.client.get(reverse('edit_bid', args=[new_bid.id])) # anon
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(response.status_code, 302)

    def test_edit_bid_redirect_home_if_bid_id_missing(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('edit_bid', args=[9999]))
        self.client.logout()
        self.assertEqual(response.url, reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_edit_bid_redirect_item_if_user_is_seller(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.2,
            return_address=self.return_address
        )
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('edit_bid', args=[new_bid.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        new_bid.delete()

    def test_edit_bid_redirect_item_if_bid_is_accepted(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.2,
            return_address=self.return_address,
            accepted=True
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('edit_bid', args=[new_bid.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(new_bid.accepted)
        new_bid.delete()

    def test_edit_bid_save_redirect_item_if_valid(self):
        new_bid_price = 0.222
        original_bid_price = 0.111
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=original_bid_price,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.post(reverse('edit_bid', args=[new_bid.id]), {
            'bid_price_xmr': new_bid_price,
            'return_address': self.return_address,
        })
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertTrue(buyer_bid)
        self.assertEqual(buyer_bid.bid_price_xmr, new_bid_price)
        new_bid.delete()

    def test_edit_bid_redirect_create_bid_if_invalid(self):
        new_bid_price = 0.222
        original_bid_price = 0.111
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=original_bid_price,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.post(reverse('edit_bid', args=[new_bid.id]), {
            'bid_price_xmr': new_bid_price,
            'return_address': 'invalid string',
        })
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('create_bid', args=[self.test_item.id]))
        self.assertEqual(buyer_bid.bid_price_xmr, original_bid_price)
        new_bid.delete()

    def test_edit_bid_returns_valid_context(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('edit_bid', args=[new_bid.id]))
        self.client.logout()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bid'].id, new_bid.id)
        self.assertTrue(response.context['form'])
        self.assertIsInstance(response.context['form'], CreateItemBidForm)
        new_bid.delete()

    ##### Delete Bid

    def test_delete_bid_redirect_home_if_bid_id_missing(self):
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('delete_bid', args=[9999]))
        self.client.logout()
        self.assertEqual(response.url, reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_delete_bid_redirect_item_if_user_not_bidder(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('delete_bid', args=[new_bid.id]))
        self.client.logout()
        self.assertEqual(response.url, reverse('get_item', args=[new_bid.item.id]))
        self.assertEqual(response.status_code, 302)

    def test_delete_bid_redirect_item_if_bid_is_accepted(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address,
            accepted=True
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('delete_bid', args=[new_bid.id]))
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(buyer_bid.accepted)

    def test_delete_bid_redirect_item_if_bid_is_deleted(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('delete_bid', args=[new_bid.id]))
        buyer_bid = ItemBid.objects.filter(bidder=self.buyer, item=self.test_item.id).first()
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(buyer_bid)

    ##### Accept Bid

    def test_accept_bid_requires_auth(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.2,
            return_address=self.return_address
        )
        response = self.client.get(reverse('accept_bid', args=[new_bid.id])) # anon
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(new_bid.accepted)

    def test_accept_bid_redirect_item_if_user_not_seller(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.client.login(username=self.buyer.username, password=self.buyer_password)
        response = self.client.get(reverse('accept_bid', args=[new_bid.id]))
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(new_bid.accepted)

    def test_accept_bid_redirect_item_if_item_not_available(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address
        )
        self.test_item.available = False
        self.test_item.save()
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('accept_bid', args=[new_bid.id]))
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(new_bid.accepted)

    def test_accept_bid_redirect_item_if_bid_accepted_already(self):
        new_bid = ItemBid.objects.create(
            item=self.test_item,
            bidder=self.buyer,
            bid_price_xmr=0.1,
            return_address=self.return_address,
            accepted=True
        )
        self.client.login(username=self.seller.username, password=self.seller_password)
        response = self.client.get(reverse('accept_bid', args=[new_bid.id]))
        self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 302)

    # def test_accept_bid_redirect_item_if_wallet_not_connected(self):
    #     new_bid = ItemBid.objects.create(
    #         item=self.test_item,
    #         bidder=self.buyer,
    #         bid_price_xmr=0.1,
    #         return_address=self.return_address
    #     )
    #     self.client.login(username=self.seller.username, password=self.seller_password)
    #     response = self.client.get(reverse('accept_bid', args=[new_bid.id]))
    #     self.assertEqual(response.url, reverse('get_item', args=[self.test_item.id]))
    #     self.assertEqual(response.status_code, 302)
    #     self.assertFalse(aw.connected)

    def test_accept_bid_updates_item_attributes(self):
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
        self.assertTrue(item_sale)
        self.assertTrue(updated_bid.accepted)
        self.assertFalse(updated_bid.item.available)
        self.assertEqual(response.url, reverse('get_sale', args=[item_sale.id]))
        self.assertEqual(response.status_code, 302)
