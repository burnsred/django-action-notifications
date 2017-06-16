# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action_notifications', '0002_auto_20170615_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnotificationpreference',
            name='is_should_notify_actor_when_target',
            field=models.BooleanField(default=False),
        ),
    ]
