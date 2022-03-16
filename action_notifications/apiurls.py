from django.conf.urls import include, url
from django.urls import re_path

from rest_framework.routers import DefaultRouter

from action_notifications import views

router = DefaultRouter()
router.register(r'action_notification', views.ActionNotificationViewSet)

urlpatterns = (
    re_path(r'^v1/', include(router.urls)),
)
