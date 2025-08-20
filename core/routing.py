# crypto_project/routing.py

from django.urls import re_path
from core import consumers

websocket_urlpatterns = [
    # 使用正则表达式的具名组 (?P<group_name>\w+) 来捕获 URL 片段
    re_path(r'ws/(?P<group_name>\w+)/$', consumers.PriceConsumer.as_asgi()),
]