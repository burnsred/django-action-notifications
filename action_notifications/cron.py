from itertools import groupby
import logging
import importlib
import kronos

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import get_template
from django.utils import timezone, translation

from . import models

logger = logging.getLogger(__name__)

ALWAYS_EMAIL_READ_NOTIFICATIONS = getattr(settings, 'ACTION_NOTIFICATION_ALWAYS_EMAIL_READ_NOTIFICATIONS', True)

TASK_DECORATOR = None
if getattr(settings, 'ACTION_NOTIFICATIONS_CRON_TASK_WRAPPER_DECORATOR', None):
    path = settings.ACTION_NOTIFICATIONS_CRON_TASK_WRAPPER_DECORATOR.split('.')
    module = importlib.import_module(path.pop(0))
    for path_component in path:
        TASK_DECORATOR = getattr(module, path_component, None)


def send_notifications_to_user(user, notifications, current_site,
                               template_notification=None):  # pylint: disable-msg=too-many-branches,
    try:
        with transaction.atomic():
            subject_template = get_template('action_notifications/notifications_email_subject.txt')
            message_text_template = get_template('action_notifications/notifications_email_message_text.txt')
            message_html_template = get_template('action_notifications/notifications_email_message_html.txt')

            context = {
                'receiver': user,
                'notifications': notifications,
                'base_url': '{}://{}'.format(
                    'http' if settings.DEBUG else 'https',
                    current_site.domain
                )
            }

            has_one_notification = len(notifications) == 1
            if template_notification:
                if template_notification.message_subject is not None:
                    subject = template_notification.message_subject
                else:
                    subject = subject_template.render(context)

                if template_notification.message_from is not None:
                    from_email = template_notification.message_from
                else:
                    from_email = settings.ACTION_NOTIFICATION_REPLY_EMAIL

                if template_notification.message_locale is not None:
                    translation.activate(template_notification.message_locale)
                else:
                    translation.deactivate_all()
            else:
                if has_one_notification and notifications[0].message_subject is not None:
                    subject = notifications[0].message_subject
                else:
                    subject = subject_template.render(context)

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

            for notification in notifications:
                for attachment in notification.message_attachments:
                    message.attach(attachment.name, attachment.read())

            message.send(fail_silently=False)
            logger.info(
                "Successfully sent emails for %s (%s)", user.get_username(), user.email
            )

            for notification in notifications:
                notification.is_emailed = True
                notification.when_emailed = timezone.now()
                notification.save()

            translation.deactivate_all()
    except Exception:
        translation.deactivate_all()
        logger.exception(
            "Failed to send notifications for user %s", user.get_username()
        )


def send_email_notifications_with_frequency(frequency):
    with transaction.atomic():
        # Grab action_verbs with this frequency
        action_verbs = models.ActionNotificationPreference.objects \
            .filter(email_notification_frequency=frequency) \
            .exclude(use_user_preference=True) \
            .values_list('action_verb', flat=True)

        read_kwargs = {}
        if not ALWAYS_EMAIL_READ_NOTIFICATIONS:
            read_kwargs['is_read'] = False

        # Find unsent notifications for the above action verbs
        unsent_notifications = models.ActionNotification.objects \
            .select_for_update() \
            .filter(
            action__verb__in=action_verbs,
            is_emailed=False,
            is_should_email=True,
            **read_kwargs
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
            logger.debug("Sending emails for %s (%s)", user.get_username(), user.email)
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
            if email_together:
                send_notifications_to_user(user, email_together, current_site)


def send_email_notification_with_user_preference():
    with transaction.atomic():
        # Grab action_verbs with this frequency
        action_verbs = models.ActionNotificationPreference.objects \
            .filter(use_user_preference=True) \
            .values_list('action_verb', flat=True)

        read_kwargs = {}
        if not ALWAYS_EMAIL_READ_NOTIFICATIONS:
            read_kwargs['is_read'] = False

        # Find all notifications, that are ready to be sent according to user preference
        unsent_notifications = models.ActionNotification.objects \
            .select_for_update() \
            .filter(
            action__verb__in=action_verbs,
            is_emailed=False,
            is_should_email=True,
            do_not_send_before__lte=timezone.now(),
            **read_kwargs,
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

            logger.debug("Sending emails for %s (%s)", user.get_username(), user.email)
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
            if email_together:
                send_notifications_to_user(user, email_together, current_site, email_together[0])


def register_email_notifications(frequency):
    '''Register a handler for the given cron string'''

    def func():
        send_email_notifications_with_frequency(frequency)

    safe_frequency = frequency.replace('*', 'star').replace(' ', '_').replace('@', '').replace('/', 'slash')
    func.__name__ = 'send_email_notifications_' + safe_frequency

    if TASK_DECORATOR:
        kronos.register(frequency)(TASK_DECORATOR(func))
    else:
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
    if TASK_DECORATOR:
        kronos.register(
            getattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCE_CRON_INTERVAL', '* * * * *')) \
            (TASK_DECORATOR(send_email_notification_with_user_preference))
    else:
        kronos.register(
            getattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCE_CRON_INTERVAL', '* * * * *')) \
            (send_email_notification_with_user_preference)
