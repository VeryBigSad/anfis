# Generated by Django 3.2.4 on 2021-12-18 17:43

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxy',
            name='proxy_scheme',
            field=models.CharField(default='http', max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='proxy',
            name='last_checked_at',
            field=models.DateTimeField(default=datetime.datetime(2021, 12, 18, 17, 43, 20, 798080, tzinfo=utc)),
        ),
    ]
