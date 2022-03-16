from django.conf import settings

try:
    from django.apps import AppConfig

    class ActionNotificationsConfig(AppConfig):
        name = 'action_notifications'
        verbose_name = 'Action Notifications'

        def ready(self):
            if getattr(settings, 'ACTION_NOTIFICATIONS_REGISTER_ON_CREATE', None):
                import action_notifications.handlers

except ImportError:
    pass
