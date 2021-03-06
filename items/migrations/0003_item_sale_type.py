# Generated by Django 2.2.10 on 2020-04-06 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0002_item_whereabouts'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='sale_type',
            field=models.CharField(choices=[('SHIPPING', 'Ship the item to a provided address.'), ('MEETING', 'Deliver the item to an agreed upon public location.')], default='ship', max_length=20),
        ),
    ]
