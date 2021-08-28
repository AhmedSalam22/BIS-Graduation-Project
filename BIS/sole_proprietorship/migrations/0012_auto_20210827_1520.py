# Generated by Django 3.1 on 2021-08-27 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0011_auto_20210819_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounts',
            name='classification',
            field=models.CharField(blank=True, choices=[('Revenue', (('Sales', 'Sales'), ('Revenue-Contra', 'Revenue-Contra'), ('Other Revenue and gains', 'Other Revenue and gains'))), ('Expenses', (('COGS', 'Cost of Goods Sold'), ('Operating Expense', 'Operating Expense'), ('Other Expenses And Losses', 'Other Expenses And Losses')))], max_length=90, null=True),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='account_type',
            field=models.CharField(choices=[('Assest', 'Assets'), ('Investment', 'Investment'), ('liabilities', 'Liabilities'), ('Revenue', 'Revenue'), ('Expenses', 'Expenses'), ('Drawings', 'Drawings')], max_length=50),
        ),
    ]
