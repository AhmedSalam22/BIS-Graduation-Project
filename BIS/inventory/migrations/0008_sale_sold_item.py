# Generated by Django 3.1 on 2021-07-04 19:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import inventory.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Customers_Sales', '0009_auto_20201127_1850'),
        ('inventory', '0007_auto_20210704_1926'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frieght_out', models.FloatField(default=0)),
                ('sales_date', models.DateField(default=inventory.models.current_date)),
                ('due_date', models.DateField(blank=True, help_text='optional if you want to specify it by yourself', null=True)),
                ('sub_total', models.FloatField(default=0)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Customers_Sales.customer')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.paymentsalesterm')),
            ],
        ),
        migrations.CreateModel(
            name='Sold_Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sale_price', models.FloatField()),
                ('quantity', models.FloatField()),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryprice')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.sale')),
            ],
        ),
    ]