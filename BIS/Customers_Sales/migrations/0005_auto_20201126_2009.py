# Generated by Django 3.1.3 on 2020-11-26 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customers_Sales', '0004_auto_20201126_1956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='account_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]