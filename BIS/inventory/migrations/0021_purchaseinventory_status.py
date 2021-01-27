# Generated by Django 3.0.7 on 2021-01-25 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_payinvoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinventory',
            name='status',
            field=models.IntegerField(choices=[(0, 'UNPAID'), (1, 'PAID')], default=1),
            preserve_default=False,
        ),
    ]