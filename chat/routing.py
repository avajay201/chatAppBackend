from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'mchat/chat/(?P<room_name>[\w-]+)/(?P<token>[\w\-\.]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'mchat/g_chat/(?P<token>[\w\-\.]+)/$', consumers.GlobalConsumer.as_asgi()),
]
