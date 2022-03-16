from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from actstream.models import Action, Follow

from action_notifications.mixins import UserPreferenceMixin
from action_notifications.models import ActionNotification, ActionNotificationPreference

@receiver(post_save, sender=Action, dispatch_uid='create_action_notification')
def create_action_notification(sender, instance, **kwargs): # pylint: disable-msg=unused-argument, too-many-locals
    action = instance
    actor = action.actor
    target = action.target
    # Bind the verb locally
    _action_verb = action.verb

    # Grab list of user ids following either the actor or the target
    follow_users = Follow.objects.filter(
        Q(content_type=ContentType.objects.get_for_model(actor), object_id=actor.pk) |
        Q(content_type=ContentType.objects.get_for_model(target), object_id=target.pk, actor_only=False)
    ).values_list('user')

    notification_preference, _ = ActionNotificationPreference.objects.get_or_create(action_verb=_action_verb)


    # Create a notification for each user
    for user in get_user_model().objects.filter(pk__in=follow_users):
        if not notification_preference.is_should_notify_actor \
                and action.actor == user \
                and ( \
                        not notification_preference.is_should_notify_actor_when_target \
                        or action.target != user \
                ):
            # Don't notify the user who did the action under these conditions
            continue
        action_notification = ActionNotification(action=action, user=user)
        action_notification.is_should_email = notification_preference.is_should_email

        if hasattr(settings, 'ACTION_NOTIFICATION_USER_PREFERENCES') \
                and notification_preference.use_user_preference:
            user_preference = getattr(
                user,
                settings.ACTION_NOTIFICATION_USER_PREFERENCE_FIELD_NAME,
                None
            )
            if user_preference:
                if not isinstance(user_preference, UserPreferenceMixin):
                    raise ImproperlyConfigured(
                        'The ACTION_NOTIFICATION_USER_PREFERENCE_FIELD_NAME in your Django setting '
                        'must inherit UserPreferenceMixin found in action_notification.mixins'
                    )
                do_not_send_before, is_should_email_separately = user_preference.get_preference_for_action_verb(
                    _action_verb,
                    action
                )
                action_notification.is_should_email_separately = is_should_email_separately
                action_notification.do_not_send_before = do_not_send_before
            else:
                action_notification.is_should_email_separately = notification_preference.is_should_email_separately
                action_notification.do_not_send_before = timezone.now()
        else:
            action_notification.is_should_email_separately = notification_preference.is_should_email_separately
        action_notification.save()
