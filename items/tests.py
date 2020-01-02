from secrets import token_urlsafe
from django.test.utils import setup_test_environment
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.paginator import Page
from django.urls import reverse
from items.models import Item, ItemImage


class ItemsTestCase(TestCase):
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

    def login(self):
        self.client.login(
            username=self.test_user_username,
            password=self.test_user_password
        )

    def logout(self):
        self.client.logout()

    def test_list_items_should_allow_anonymous(self):
        response = self.client.get(reverse('list_items'))
        self.assertEqual(response.status_code, 200)

    def test_get_item_should_allow_anonymous(self):
        response = self.client.get(reverse('get_item', args=[self.test_item.id]))
        self.assertEqual(response.status_code, 200)

    def test_list_items_returns_page(self):
        response = self.client.get(reverse('list_items'))
        items = response.context['items']
        self.assertTrue(isinstance(items, Page))

    def test_create_item_should_require_auth(self):
        no_auth_response = self.client.get(reverse('create_item'))
        self.login()
        auth_response = self.client.get(reverse('create_item'))
        self.logout()
        self.assertEqual(no_auth_response.status_code, 302)
        self.assertTrue(no_auth_response.url.startswith('/accounts/login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_edit_item_should_require_auth(self):
        no_auth_response = self.client.get(reverse('edit_item', args=[self.test_item.id]))
        self.login()
        auth_response = self.client.get(reverse('edit_item', args=[self.test_item.id]))
        self.logout()
        self.assertEqual(no_auth_response.status_code, 302)
        self.assertTrue(no_auth_response.url.startswith('/accounts/login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_edit_item_should_require_active_user_is_owner(self):
        new_user = User.objects.create_user(
            'tester2',
            password=token_urlsafe(24)
        )
        new_item = Item.objects.create(
            owner=new_user,
            name='Test Item 2',
            description='Test item 2',
            ask_price_xmr=0.3
        )
        self.login()
        test_item_edit_response = self.client.get(reverse('edit_item', args=[self.test_item.id]))
        new_item_edit_response = self.client.get(reverse('edit_item', args=[new_item.id]))
        self.logout()
        self.assertEqual(test_item_edit_response.status_code, 200)
        self.assertEqual(new_item_edit_response.status_code, 302)
        new_item.delete()
        new_user.delete()

    def test_delete_item_should_require_auth(self):
        no_auth_response = self.client.get(reverse('delete_item', args=[self.test_item.id]))
        self.login()
        auth_response = self.client.get(reverse('delete_item', args=[self.test_item.id]))
        self.logout()
        self.assertEqual(no_auth_response.status_code, 302)
        self.assertTrue(no_auth_response.url.startswith('/accounts/login'))

    def test_delete_item_should_require_active_user_is_owner(self):
        new_user = User.objects.create_user(
            'tester3',
            password=token_urlsafe(24)
        )
        new_item = Item.objects.create(
            owner=new_user,
            name='Test Item 3',
            description='Test item 3',
            ask_price_xmr=0.3
        )
        self.login()
        test_delete_item_response = self.client.get(reverse('delete_item', args=[self.test_item.id]))
        new_delete_item_response = self.client.get(reverse('delete_item', args=[new_item.id]))
        self.logout()
        self.assertEqual(test_delete_item_response.status_code, 302)
        self.assertEqual(new_delete_item_response.status_code, 302)
        new_item.delete()
        new_user.delete()
