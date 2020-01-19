from secrets import token_urlsafe
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.core.files import File
from items.models import Item, ItemImage


class ItemModelsTestCase(TestCase):
    def setUp(self):
        self.test_user_username = 'tester'
        self.test_user_password = token_urlsafe(32)
        self.test_user = User.objects.create_user(
            self.test_user_username,
            password=self.test_user_password
        )
        self.test_item = Item.objects.create(
            owner=self.test_user,
            name='Test Item',
            description='Test item',
            ask_price_xmr=0.3
        )


    def test_create_item(self):
        test_item = Item.objects.create(
            owner=self.test_user,
            name='Test Item',
            description='Test item',
            ask_price_xmr=0.3
        )
        obj_name = f'{test_item.id} - {test_item.owner} - {test_item.name}'
        self.assertTrue(isinstance(test_item, Item))
        self.assertEqual(test_item.__str__(), obj_name)

    # def test_create_item_image(self):
    #     static_img = finders.find('images/monero-symbol-800.png')
    #     img = File(open(static_img, 'rb'))
    #     test_item_image = ItemImage.objects.create(
    #         item=self.test_item,
    #         image=img
    #     )
    #     obj_name = f'{self.id} - {self.item.name} - {self.id}'
