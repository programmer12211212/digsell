import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .permissions import is_admin_user
from .services import get_recent_activities, get_admin_notifications


class StaffConsumerMixin:
    @database_sync_to_async
    def is_staff_user(self):
        user = self.scope.get('user')
        return is_admin_user(user)


class ActivityConsumer(StaffConsumerMixin, AsyncWebsocketConsumer):
    async def connect(self):
        if not await self.is_staff_user():
            await self.close()
            return
        self.group_name = 'admin_activity'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        activities = await database_sync_to_async(get_recent_activities)(limit=15)
        await self.send(text_data=json.dumps({'type': 'activity_snapshot', 'items': activities}))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def activity_update(self, event):
        await self.send(text_data=json.dumps(event['payload']))


class NotificationConsumer(StaffConsumerMixin, AsyncWebsocketConsumer):
    async def connect(self):
        if not await self.is_staff_user():
            await self.close()
            return
        self.group_name = 'admin_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        data = await database_sync_to_async(get_admin_notifications)(self.scope['user'])
        await self.send(text_data=json.dumps({'type': 'notification_snapshot', **data}))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_update(self, event):
        await self.send(text_data=json.dumps(event['payload']))
