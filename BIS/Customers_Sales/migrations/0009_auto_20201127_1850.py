# Generated by Django 3.1.3 on 2020-11-27 16:50

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Customers_Sales', '0008_auto_20201127_1846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customernote',
            name='note',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]