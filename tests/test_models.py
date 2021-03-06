from django.test import TestCase
from django.contrib.auth.models import User, Group

from mock import patch

from actstream import action
from actstream.actions import follow
from actstream.registry import register, unregister

from action_notifications import models

class BaseTestCase(TestCase):
    def setUp(self):
        register(User)
        register(Group)

        self.user1 = User.objects.create_user('test1', 'test1@example.com')
        self.user2 = User.objects.create_user('test2', 'test1@example.com')
        self.group = Group.objects.create(name='Test Group')

class ActionNotificationTestCase(BaseTestCase):
    def setUp(self):
        super(ActionNotificationTestCase, self).setUp()

        follow(self.user1, self.group, actor_only=False)
        action.send(
            self.user2,
            verb='gyred and gimbled in',
            target=self.group
        )

    def test_str(self):
        action_notification = models.ActionNotification.objects.all()[0]
        self.assertEqual(
            action_notification.__str__(),
            'test2 gyred and gimbled in Test Group 0 minutes ago (unread)'
        )

    def test_create_on_action(self):
        self.assertEqual(models.ActionNotification.objects.all().count(), 1)

        action_notification = models.ActionNotification.objects.all()[0]
        self.assertEqual(action_notification.user, self.user1)
        self.assertEqual(action_notification.action.target, self.group)
        self.assertEqual(action_notification.is_read, False)
        self.assertEqual(action_notification.is_emailed, False)

    @patch('action_notifications.models.default_pusher')
    def test_pusher(self, default_pusher_mock):
        action.send(
            self.user2,
            verb='gyred and gimbled in',
            target=self.group
        )
        default_pusher_mock.trigger.assert_called_with(
            'private-user-notifications-test1',
            'new-notification',
            {}
        )

class ActionNotificationPreferenceTestCase(BaseTestCase):
    def test_str(self):
        preference = models.ActionNotificationPreference.objects.create(
            action_verb='gyred and gimbled in',
            is_should_email=True
        )
        self.assertEqual(preference.__str__(), 'notification preference for "gyred and gimbled in"')

    def test_email_preference(self):
        follow(self.user1, self.group, actor_only=False)

        models.ActionNotificationPreference.objects.create(
            action_verb='gyred and gimbled in',
            is_should_email=True
        )

        action.send(
            self.user2,
            verb='gyred and gimbled in',
            target=self.group
        )
        action.send(
            self.user2,
            verb='gimbled and gyred in',
            target=self.group
        )
        action_notification_1 = models.ActionNotification.objects.get(action__verb='gyred and gimbled in')
        action_notification_2 = models.ActionNotification.objects.get(action__verb='gimbled and gyred in')

        # Has a preference, should be true
        self.assertEqual(action_notification_1.is_should_email, True)

        # Has no preference, should be false by default
        self.assertEqual(action_notification_2.is_should_email, False)

    def test_is_should_notify_actor(self):
        follow(self.user1, self.user1, actor_only=False)

        preference = models.ActionNotificationPreference.objects.create(action_verb='gyred and gimbled in')

        preference.is_should_notify_actor = False
        preference.save()
        action.send(self.user1, verb='gyred and gimbled in', target=self.group)
        self.assertFalse(models.ActionNotification.objects.filter(action__verb='gyred and gimbled in').exists())

        preference.is_should_notify_actor = True
        preference.save()
        action.send(self.user1, verb='gyred and gimbled in', target=self.group)
        self.assertTrue(models.ActionNotification.objects.filter(action__verb='gyred and gimbled in').exists())

    def test_is_should_notify_actor_when_target(self):
        follow(self.user1, self.user1, actor_only=False)

        preference = models.ActionNotificationPreference.objects.create(action_verb='gyred and gimbled in')

        preference.is_should_notify_actor_when_target = False
        preference.save()
        action.send(self.user1, verb='gyred and gimbled in', target=self.user1)
        self.assertFalse(models.ActionNotification.objects.filter(action__verb='gyred and gimbled in').exists())

        preference.is_should_notify_actor_when_target = True
        preference.save()
        action.send(self.user1, verb='gyred and gimbled in', target=self.user1)
        self.assertTrue(models.ActionNotification.objects.filter(action__verb='gyred and gimbled in').exists())
