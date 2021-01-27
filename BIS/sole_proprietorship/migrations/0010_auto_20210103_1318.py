# Generated by Django 3.0.7 on 2021-01-03 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0009_auto_20210103_1315'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='accounts',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='accounts',
            constraint=models.UniqueConstraint(fields=('account', 'owner'), name='unique_account'),
        ),
    ]