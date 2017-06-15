# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action_notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnotification',
            name='is_should_email_separately',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='actionnotification',
            name='when_emailed',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='actionnotificationpreference',
            name='is_should_email_separately',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='actionnotificationpreference',
            name='is_should_notify_actor',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='actionnotificationpreference',
            name='action_verb',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='actionnotificationpreference',
            name='email_notification_frequency',
            field=models.CharField(default=b'@daily', max_length=64, choices=[(b'* * * * *', b'Immediately'), (b'*/30 * * * *', b'Every 30 minutes'), (b'@daily', b'Daily')]),
        ),
        migrations.AlterField(
            model_name='actionnotificationpreference',
            name='is_should_email',
            field=models.BooleanField(default=False),
        ),
    ]
