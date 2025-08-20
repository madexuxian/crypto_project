# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 从 URL 中获取群组名称
        # 例如 /ws/price_spread/ -> price_spread
        # 例如 /ws/triangular_arbitrage/ -> triangular_arbitrage
        self.room_group_name = self.scope['url_route']['kwargs'].get('group_name', 'default_group')

        # 加入群组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开群组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # --- 这里是关键的新增部分 ---

    # 从 'price_spread' 群组接收消息的处理方法
    # 这个方法名 'price_update' 必须与 stream_trades.py 中指定的 type 一致
    async def price_update(self, event):
        message = event['message']

        # 将消息发送到 WebSocket
        await self.send(text_data=json.dumps(message))

    # 从 'triangular_arbitrage' 群组接收消息的处理方法
    # 这个方法名 'arbitrage_update' 必须与 stream_trades.py 中指定的 type 一致
    async def arbitrage_update(self, event):
        message = event['message']

        # 将消息发送到 WebSocket
        await self.send(text_data=json.dumps(message))