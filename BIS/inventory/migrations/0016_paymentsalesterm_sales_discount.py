# Generated by Django 3.1 on 2021-07-15 16:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0007_auto_20210714_1945'),
        ('inventory', '0015_auto_20210715_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentsalesterm',
            name='sales_discount',
            field=models.ForeignKey(default=1, help_text='Select Sales discount account', on_delete=django.db.models.deletion.CASCADE, related_name='sales_discount', to='sole_proprietorship.accounts'),
            preserve_default=False,
        ),
    ]
