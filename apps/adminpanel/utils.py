from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.security.models import AuditLog


def log_admin_action(admin, action, model_name='', object_id='', changes=None):
    AuditLog.objects.create(
        admin=admin,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        changes=changes or {},
    )


def broadcast_activity(payload):
    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(
        'admin_activity',
        {'type': 'activity_update', 'payload': payload},
    )


def broadcast_notification(payload):
    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(
        'admin_notifications',
        {'type': 'notification_update', 'payload': payload},
    )
