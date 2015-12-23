from rest_framework import serializers

from actstream.models import Action

from action_notifications import models

class ActionSerializer(serializers.ModelSerializer):
    actor = serializers.CharField()
    verb = serializers.CharField()
    target = serializers.CharField()
    action_object = serializers.CharField()
    data = serializers.DictField()

    class Meta:
        fields = ('actor', 'verb', 'target', 'action_object', 'data',)
        model = Action

    def get_text(self, obj):
        return obj.__str__()

class ActionNotificationSerializer(serializers.ModelSerializer):
    action = ActionSerializer(read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = models.ActionNotification
