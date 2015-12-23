from django.contrib import admin

from action_notifications import messages, models

class ActionNotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'is_should_email', 'is_read', 'is_emailed', 'created',)
    search_fields = ('user__first_name', 'user__last_name',)
    list_per_page = 20

    def message(self, obj):
        return messages.get_message(obj.action, receiver=obj.user)

class ActionNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('action_verb', 'is_should_email', 'email_notification_frequency',)

admin.site.register(models.ActionNotification, ActionNotificationAdmin)
admin.site.register(models.ActionNotificationPreference, ActionNotificationPreferenceAdmin)
