from django.test import TestCase
from items.forms import CreateItemForm, SearchItemForm
from core.monero import AuctionWallet


class ItemFormsTestCase(TestCase):
    def setUp(self):
        self.aw = AuctionWallet()

    def test_create_item_form_is_valid(self):
        data = {
            'name': 'Expected item name',
            'description': 'expected description',
            'whereabouts': 'anywhere in the world',
            'ask_price_xmr': .1,
            'payout_address': self.aw.wallet.accounts[0].address(),
        }
        form = CreateItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_search_item_form_is_valid(self):
        data = {
            'search': ''
        }
        form = SearchItemForm(data=data)
        self.assertTrue(form.is_valid())

