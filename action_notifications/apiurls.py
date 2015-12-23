from django.conf.urls import patterns, include, url

from rest_framework.routers import DefaultRouter

from action_notifications import views

router = DefaultRouter()
router.register(r'action_notification', views.ActionNotificationViewSet)

urlpatterns = patterns('',
    url(r'^v1/', include(router.urls)),
)