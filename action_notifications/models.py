from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from actstream.models import Action, Follow

try:
    from br_pusher import default_pusher
except ImportError:
    default_pusher = None

class ActionNotification(models.Model):
    action = models.ForeignKey(Action)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, related_name='+')

    is_should_email = models.BooleanField(default=False, db_index=True)

    is_read = models.BooleanField(default=False, db_index=True)
    is_emailed = models.BooleanField(default=False, db_index=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-action__timestamp',)
        unique_together = (
            ('action', 'user',),
        )

    def __unicode__(self):
        return u'{} ({})'.format(
            self.action.__unicode__(),
            'read' if self.is_read else 'unread'
        )

class ActionNotificationPreference(models.Model):
    EMAIL_NOTIFICATION_FREQUENCIES = (
        ('*/30 * * * *', 'Every 30 minutes',),
        ('@daily', 'Daily',),
    )

    action_verb = models.CharField(max_length=255, unique=True, blank=True)
    is_should_email = models.BooleanField()

    email_notification_frequency = models.CharField(
        max_length=64,
        choices=EMAIL_NOTIFICATION_FREQUENCIES,
        default='@daily'
    )

    def __unicode__(self):
        return u'notification preference for "{}"'.format(self.action_verb)

@receiver(post_save, sender=Action)
def create_action_notification(sender, instance, **kwargs): # pylint: disable-msg=unused-argument
    action = instance
    actor = action.actor
    target = action.target

    # Grab list of user ids following either the actor or the target
    follow_users = Follow.objects.filter(
        Q(content_type=ContentType.objects.get_for_model(actor), object_id=actor.pk) |
        Q(content_type=ContentType.objects.get_for_model(target), object_id=target.pk, actor_only=False)
    ).values_list('user')

    # Create a notification for each user
    for user in get_user_model().objects.filter(pk__in=follow_users):
        # Don't notify the user who did the action
        if action.actor == user:
            continue

        action_notification = ActionNotification(
            action=action,
            user=user
        )

        try:
            notification_preference = ActionNotificationPreference.objects.get(action_verb=action.verb)
            action_notification.is_should_email = notification_preference.is_should_email
        except ActionNotificationPreference.DoesNotExist, _:
            action_notification.is_should_email = False

        action_notification.save()

        if default_pusher is not None:
            channel_name = "private-user-notifications-{}".format(user.get_username())
            default_pusher.trigger(channel_name, 'new-notification', {})
