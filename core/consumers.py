# core/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class PriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 只有登录的用户才能连接
        if self.scope["user"].is_authenticated:
            self.room_group_name = 'price_spread'
            # 加入一个Channel Group，所有加入该组的consumer都能收到消息
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"User {self.scope['user']} connected to WebSocket.")
        else:
            await self.close()
            logger.warning("Unauthenticated user tried to connect to WebSocket.")

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"User {self.scope['user']} disconnected.")

    # 这个方法的名字 `price_update` 对应于 channel_layer.group_send 中的 'type'
    async def price_update(self, event):
        message = event['message']
        # 将从group收到的消息原样发送给前端的WebSocket客户端
        await self.send(text_data=json.dumps(message))
