from itertools import groupby
import sys

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template import Context
from django.template.loader import get_template

import kronos

from action_notifications import models

def send_email_notifications_with_frequency(frequency):
    with transaction.atomic():
        # Grab action_verbs with this frequency
        action_verbs = models.ActionNotificationPreference.objects \
            .filter(email_notification_frequency=frequency) \
            .values_list('action_verb', flat=True)

        # Find unsent notifications for the above action verbs
        unsent_notifications = models.ActionNotification.objects \
            .select_for_update() \
            .filter(
                action__verb__in=action_verbs,
                is_read=False,
                is_emailed=False,
                is_should_email=True
            ) \
            .prefetch_related(
                'action',
                'user'
            ) \
            .order_by('-created')

        unsent_notifications = sorted(unsent_notifications, key=lambda notification: notification.user)
        notifications_by_user = groupby(unsent_notifications, key=lambda notification: notification.user)

        current_site = Site.objects.get_current()

        for user, notifications in notifications_by_user:
            if not user.email:
                continue

            try:
                with transaction.atomic():
                    notifications = list(notifications)

                    subject_template = get_template('action_notifications/notifications_email_subject.txt')
                    message_text_template = get_template('action_notifications/notifications_email_message_text.txt')
                    message_html_template = get_template('action_notifications/notifications_email_message_html.txt')

                    context = Context({
                        'receiver': user,
                        'notifications': notifications,
                        'base_url': '{}://{}'.format(
                            'http' if settings.DEBUG else 'https',
                            current_site.domain
                        )
                    })

                    message = EmailMultiAlternatives(
                        subject_template.render(context),
                        message_text_template.render(context),
                        settings.ACTION_NOTIFICATION_REPLY_EMAIL,
                        [user.email]
                    )
                    message.attach_alternative(message_html_template.render(context), 'text/html')
                    message.send(fail_silently=False)

                    for notification in notifications:
                        notification.is_emailed = True
                        notification.save()
            except Exception as e:
                print >> sys.stderr, e

    return

def register_email_notifications(frequency):
    '''Register a handler for the given cron string'''
    def func():
        send_email_notifications_with_frequency(frequency)

    safe_frequency = frequency.replace('*', 'star').replace(' ', '_').replace('@', '').replace('/', 'slash')
    func.__name__ = 'send_email_notifications_' + safe_frequency

    kronos.register(frequency)(func)

for frequency, _ in models.ActionNotificationPreference.EMAIL_NOTIFICATION_FREQUENCIES:
    register_email_notifications(frequency)
