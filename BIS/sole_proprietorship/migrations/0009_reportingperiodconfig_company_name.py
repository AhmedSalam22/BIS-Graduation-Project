# Generated by Django 3.1 on 2021-08-02 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sole_proprietorship', '0008_auto_20210715_1801'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportingperiodconfig',
            name='company_name',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]