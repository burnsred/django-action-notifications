from django.contrib import admin

from action_notifications import models


class ActionNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'message_body',
        'message_subject',
        'user',
        'is_should_email',
        'is_should_email_separately',
        'is_read',
        'is_emailed',
        'created',
    )
    search_fields = ('user__first_name', 'user__last_name',)
    list_per_page = 20


class ActionNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'action_verb',
        'is_should_notify_actor',
        'is_should_notify_actor_when_target',
        'is_should_email',
        'is_should_email_separately',
        'email_notification_frequency',
    )


admin.site.register(models.ActionNotification, ActionNotificationAdmin)
admin.site.register(models.ActionNotificationPreference, ActionNotificationPreferenceAdmin)
