from random import choice
from secrets import token_urlsafe
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.auth.models import User
from items.models import Item
from bids.models import ItemBid


class Command(BaseCommand):
    help = 'Generates fake items within the application for testing'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--items', type=int, help='Number of items to create', default=5)

    def handle(self, *args, **kwargs):
        dummy_data = {
            'item_names': [
                'Do Androids Dream of Electric Sheep?',
                'The Hitchhiker\'s Guide to the Galaxy',
                'Something Wicked This Way Comes',
                'Pride and Prejudice and Zombies',
                'The Curious Incident of the Dog in the Night-Time',
                'I Was Told There\'d Be Cake',
                'To Kill a Mockingbird',
                'The Unbearable Lightness of Being',
                'Eats, Shoots & Leaves: The Zero Tolerance Approach to Punctuation',
                'The Hollow Chocolate Bunnies of the Apocalypse',
                'A Clockwork Orange',
                'Are You There, Vodka? It\'s Me, Chelsea'
            ],
            'item_descriptions': [
                'Brand new, never opened or used.',
                'Light usage, good condition',
                'Spilled some water on it, fair condition, but good enough',
                'Mint condition - collectors item'
            ],
            'item_ask_price': [
                '.1', '.23', '.51', '.233', '.47', '.09'
            ],
            'new_items': []
        }

        for index,value in enumerate(range(kwargs['items'])):
            random_item = choice(dummy_data['item_names'])
            random_desc = choice(dummy_data['item_descriptions'])
            random_price = choice(dummy_data['item_ask_price'])
            random_user = choice(User.objects.all())

            item = Item(
                owner=random_user,
                name=random_item,
                description=random_desc,
                ask_price_xmr=random_price,
            )
            item.save()

            dummy_data['new_items'].append(item)
            self.stdout.write(self.style.SUCCESS(f'Item "{item.name} ({item.id})" created successfully!'))

        for i in dummy_data['new_items']:
            all_users = User.objects.all().exclude(username=i.owner.username)
            for u in all_users:
                bid = ItemBid(
                    item=i,
                    bidder=u,
                    bid_price_xmr=i.ask_price_xmr
                )
                bid.save()
                self.stdout.write(self.style.SUCCESS(f'Bid #{bid.id} for user "{bid.bidder}" created successfully!'))
