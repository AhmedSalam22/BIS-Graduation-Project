# Generated by Django 3.0.7 on 2021-01-16 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20210114_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinventory',
            name='frieght_in',
            field=models.FloatField(default=0),
        ),
    ]