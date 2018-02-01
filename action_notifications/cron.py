from itertools import groupby
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone, translation


import kronos

from . import models

logger = logging.getLogger(__name__)


def send_notifications_to_user(user, notifications, current_site):
    try:
        with transaction.atomic():
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

            has_one_notification = len(notifications) == 1

            subject = None
            if has_one_notification and notifications[0].message_subject is not None:
                subject = notifications[0].message_subject
            else:
                subject = subject_template.render(context)

            from_email = None
            if has_one_notification and notifications[0].message_from is not None:
                from_email = notifications[0].message_from
            else:
                from_email = settings.ACTION_NOTIFICATION_REPLY_EMAIL

            if has_one_notification and notifications[0].message_locale is not None:
                translation.activate(notifications[0].message_locale)
            else:
                translation.deactivate_all()

            message = EmailMultiAlternatives(
                subject,
                message_text_template.render(context),
                from_email,
                [user.email]
            )
            message.attach_alternative(message_html_template.render(context), 'text/html')
            message.send(fail_silently=False)

            for notification in notifications:
                notification.is_emailed = True
                notification.when_emailed = timezone.now()
                notification.save()

            translation.deactivate_all()
    except Exception:
        translation.deactivate_all()
        logger.exception('Failed to send notifications for user %s', user.username)


def send_email_notifications_with_frequency(frequency):
    with transaction.atomic():
        # Grab action_verbs with this frequency
        action_verbs = models.ActionNotificationPreference.objects \
            .filter(email_notification_frequency=frequency) \
            .exclude(use_user_preference=True) \
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
            logger.debug('Sending emails for %s (%s)', user.username, user.email)
            notifications = list(notifications)

            email_separately = [
                notification
                for notification in notifications
                if notification.is_should_email_separately
            ]
            email_together = [
                notification
                for notification in notifications
                if not notification.is_should_email_separately
            ]
            for notification in email_separately:
                send_notifications_to_user(user, [notification], current_site)
            if len(email_together) > 0:
                send_notifications_to_user(user, email_together, current_site)


def send_email_notification_with_user_preference():
    with transaction.atomic():
        # Grab action_verbs with this frequency
        action_verbs = models.ActionNotificationPreference.objects \
            .filter(use_user_preference=True) \
            .values_list('action_verb', flat=True)

        # Find all notifications, that are ready to be send according to user preference
        unsent_notifications = models.ActionNotification.objects \
            .select_for_update() \
            .filter(
            action__verb__in=action_verbs,
            is_read=False,
            is_emailed=False,
            is_should_email=True,
            do_not_send_before__lte=timezone.now()
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

            logger.debug('Sending emails for %s (%s)', user.username, user.email)
            notifications = list(notifications)

            email_separately = [
                notification
                for notification in notifications
                if notification.is_should_email_separately
            ]
            email_together = [
                notification
                for notification in notifications
                if not notification.is_should_email_separately
            ]
            for notification in email_separately:
                send_notifications_to_user(user, [notification], current_site)
            if len(email_together) > 0:
                send_notifications_to_user(user, email_together, current_site)

def register_email_notifications(frequency):
    '''Register a handler for the given cron string'''
    def func():
        send_email_notifications_with_frequency(frequency)

    safe_frequency = frequency.replace('*', 'star').replace(' ', '_').replace('@', '').replace('/', 'slash')
    func.__name__ = 'send_email_notifications_' + safe_frequency

    kronos.register(frequency)(func)

for frequency, _ in models.ActionNotificationPreference.EMAIL_NOTIFICATION_FREQUENCIES:
    register_email_notifications(frequency)

if getattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCES', None):
    if not hasattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCE_FIELD_NAME'):
        raise ImproperlyConfigured(
            'You must set the ACTION_NOTIFICATION_USER_PREFERENCE_FIELD_NAME in your Django setting '
            'file:\nSpecify a field name on the User model that inherits the UserPreferenceMixin Class found'
            'in action_notification.mixins and implements all abstract methods'
        )
    kronos.register(
        getattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCE_CRON_INTERVAL', '* * * * *'))\
        (send_email_notification_with_user_preference)