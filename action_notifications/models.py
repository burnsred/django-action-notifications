from django.db import models
from django.conf import settings

from actstream.models import Action

from . import messages

class ActionNotification(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, related_name='+', on_delete=models.CASCADE)

    is_should_email = models.BooleanField(default=False, db_index=True)
    is_should_email_separately = models.BooleanField(default=False)

    is_read = models.BooleanField(default=False, db_index=True)
    is_emailed = models.BooleanField(default=False, db_index=True)

    do_not_send_before = models.DateTimeField(blank=True, null=True)
    when_emailed = models.DateTimeField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-action__timestamp',)
        unique_together = (
            ('action', 'user',),
        )

    def __str__(self):
        return u'{} ({})'.format(
            self.action.__str__(),
            'read' if self.is_read else 'unread'
        )

    def _load_message(self):
        if not hasattr(self, '_message'):
            self._message = messages.get_message(self.action, self.user)

    @property
    def message_body(self):
        self._load_message()
        return self._message[0]

    @property
    def message_subject(self):
        self._load_message()
        return self._message[1]

    @property
    def message_from(self):
        self._load_message()
        if len(self._message) > 2:
            return self._message[2]
        return None

    @property
    def message_locale(self):
        self._load_message()
        if len(self._message) > 3:
            return self._message[3]
        return None


class ActionNotificationPreference(models.Model):
    EMAIL_NOTIFICATION_FREQUENCIES = (
        ('* * * * *', 'Immediately',),
        ('*/30 * * * *', 'Every 30 minutes',),
        ('@daily', 'Daily',),
    )

    action_verb = models.CharField(max_length=255, unique=True)

    is_should_notify_actor = models.BooleanField(default=False)
    is_should_notify_actor_when_target = models.BooleanField(default=False)

    # Email preferences
    is_should_email = models.BooleanField(default=False)
    is_should_email_separately = models.BooleanField(default=False)
    follow_topic = models.CharField(
        default='',
        blank=True,
        max_length=255,
        help_text='If a topic is set, only follow relationships with that topic are selected'
    )
    use_user_preference = models.BooleanField(
        default=False,
        help_text='Setting this true will cause frequency and is_email_separately to be ignored'
    )
    email_notification_frequency = models.CharField(
        max_length=64,
        choices=EMAIL_NOTIFICATION_FREQUENCIES,
        default='@daily'
    )

    def __str__(self):
        return u'notification preference for "{}"'.format(self.action_verb)
