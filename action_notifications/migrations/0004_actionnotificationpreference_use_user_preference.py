# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action_notifications', '0003_actionnotificationpreference_is_should_notify_actor_when_target'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnotificationpreference',
            name='use_user_preference',
            field=models.BooleanField(default=False, help_text=b'Setting this true will cause frequency and is_email_separately to be ignored'),
        ),
    ]
