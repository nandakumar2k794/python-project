import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query = self.scope.get("query_string", b"").decode()
        uid = "anon"
        if "uid=" in query:
            uid = query.split("uid=", 1)[1].split("&", 1)[0]
        self.group = f"user_{uid}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
