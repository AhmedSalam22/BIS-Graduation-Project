# Generated by Django 3.2.6 on 2021-10-04 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0017_auto_20210911_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounts',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]