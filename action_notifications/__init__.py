from django.conf import settings

from django.contrib.auth.models import Group
from django.core.mail import send_mail

default_app_config = 'action_notifications.apps.ActionNotificationsConfig'

def send_notification(subject, message, sender, receivers, all_notifications_group_name):
    update_group, _ = Group.objects.get_or_create(name=all_notifications_group_name)

    if settings.DEBUG:
        # Only send to the notification group
        receivers = update_group.user_set.values_list('email', flat=True)
    else:
        # Add to list of receivers
        receivers += update_group.user_set.values_list('email', flat=True)

    send_mail(subject, message, sender, receivers, fail_silently=False)

def send_user_notification(subject_template, message_template, context, receivers, sender=None):
    for receiver in set(receivers):
        if not receiver.email:
            continue

        context.push()

        context['receiver'] = receiver
        send_mail(
            subject_template.render(context),
            message_template.render(context),
            sender or 'noreply@clough.com.au',
            [receiver.email],
            fail_silently=False
        )

        context.pop()
