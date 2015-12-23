# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('actstream', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_should_email', models.BooleanField(default=False, db_index=True)),
                ('is_read', models.BooleanField(default=False, db_index=True)),
                ('is_emailed', models.BooleanField(default=False, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(to='actstream.Action')),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-action__timestamp',),
            },
        ),
        migrations.CreateModel(
            name='ActionNotificationPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_verb', models.CharField(unique=True, max_length=255, blank=True)),
                ('is_should_email', models.BooleanField()),
                ('email_notification_frequency', models.CharField(default=b'@daily', max_length=64, choices=[(b'*/30 * * * *', b'Every 30 minutes'), (b'@daily', b'Daily')])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='actionnotification',
            unique_together=set([('action', 'user')]),
        ),
    ]
