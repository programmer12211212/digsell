from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/admin/activity/', consumers.ActivityConsumer.as_asgi()),
    path('ws/admin/notifications/', consumers.NotificationConsumer.as_asgi()),
]
