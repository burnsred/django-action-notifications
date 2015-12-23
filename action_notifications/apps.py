try:
    from django.apps import AppConfig

    class ActionNotificationsConfig(AppConfig):
        name = 'action_notifications'
        verbose_name = 'Action Notifications'
except ImportError:
    pass
