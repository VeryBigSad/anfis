# Generated by Django 3.2.4 on 2021-07-01 01:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0002_log'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='user',
        ),
        migrations.DeleteModel(
            name='Arcgis',
        ),
        migrations.DeleteModel(
            name='Location',
        ),
    ]