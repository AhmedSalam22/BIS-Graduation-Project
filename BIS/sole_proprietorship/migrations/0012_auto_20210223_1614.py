# Generated by Django 3.1 on 2021-02-23 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0011_auto_20210131_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journal',
            name='status',
            field=models.IntegerField(choices=[(1, 'Purchase Inventory'), (2, 'Purchase return'), (3, 'Purchase Allowance'), (4, 'Freight in')], null=True),
        ),
    ]
