# core/routing.py
from django.urls import path # 更改了导入
from . import consumers

websocket_urlpatterns = [
    # 为了更稳定地匹配，将 re_path 更改为 path
    path('ws/price_data/', consumers.PriceConsumer.as_asgi()),
]