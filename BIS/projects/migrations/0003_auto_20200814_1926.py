# Generated by Django 3.1 on 2020-08-14 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20200814_1707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projects',
            name='img',
            field=models.ImageField(blank=True, upload_to='media/projects'),
        ),
    ]