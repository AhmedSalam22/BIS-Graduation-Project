# Generated by Django 3.1.5 on 2021-01-30 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suppliers', '0002_auto_20210130_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='middle_name',
            field=models.CharField(blank=True, default=' ', max_length=50),
        ),
    ]
