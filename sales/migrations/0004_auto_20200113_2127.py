# Generated by Django 2.2.8 on 2020-01-13 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_itemsale_sale_cancelled'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemsale',
            name='network_fee_xmr',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='itemsale',
            name='seller_payout_transaction',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]