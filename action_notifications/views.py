from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, pagination, permissions, decorators
from rest_framework.response import Response
import django_filters

from action_notifications import models, serializers

class ActionNotificationPagination(pagination.CursorPagination):
    page_size = 10

class ActionNotificationFilterSet(django_filters.FilterSet):
    app_label = django_filters.MethodFilter(action='filter_app_label')

    class Meta:
        model = models.ActionNotification
        fields = ('app_label',)

    def filter_app_label(self, queryset, value):
        app_content_types = ContentType.objects.filter(app_label=value)

        return queryset.filter(
            Q(action__actor_content_type__in=app_content_types) |
            Q(action__target_content_type__in=app_content_types)
        )

class ActionNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.ActionNotification.objects.all()
    ordering_fields = ('created',)
    ordering = ('-created',)

    filter_class = ActionNotificationFilterSet

    serializer_class = serializers.ActionNotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ActionNotificationPagination

    def get_queryset(self):
        '''Gets the query set, restricting to just those belonging to the
        current user'''

        return models.ActionNotification.objects.all().prefetch_related(
            'action',
            'action__actor',
            'action__target',
            'user'
        ).filter(
            user=self.request.user
        )

    @decorators.list_route(methods=['post'])
    def mark_read(self, request): # pylint: disable-msg=unused-argument
        updated_count = self.get_queryset() \
            .filter(is_read=False) \
            .update(is_read=True)

        return Response({ 'updated_count': updated_count })
