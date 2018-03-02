# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action_notifications', '0004_actionnotificationpreference_use_user_preference'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnotification',
            name='do_not_send_before',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
