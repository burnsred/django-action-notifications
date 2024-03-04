from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import get_template
from django.utils import timezone, translation

from .logger import logger

def send_notifications_to_user(
    user,
    notifications,
    current_site,
    template_notification=None
):  # pylint: disable-msg=too-many-branches,
    try:
        with transaction.atomic():
            subject_template = get_template(
                'action_notifications/notifications_email_subject.txt')
            message_text_template = get_template(
                'action_notifications/notifications_email_message_text.txt')
            message_html_template = get_template(
                'action_notifications/notifications_email_message_html.txt')

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
            message.attach_alternative(
                message_html_template.render(context), 'text/html')

            for notification in notifications:
                for attachment in notification.message_attachments:
                    message.attach(attachment.name, attachment.read())

            message.send(fail_silently=False)
            logger.info('Successfully sent emails for %s (%s)',
                        user.username, user.email)

            for notification in notifications:
                notification.is_emailed = True
                notification.when_emailed = timezone.now()
                notification.save()

            translation.deactivate_all()
    except Exception:
        translation.deactivate_all()
        logger.exception(
            'Failed to send notifications for user %s', user.username)
