from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'mchat/chat/(?P<room_name>[\w-]+)/(?P<token>[\w\-\.]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'mchat/g_chat/(?P<token>[\w\-\.]+)/$', consumers.GlobalConsumer.as_asgi()),
    re_path(r'mcall/call/(?P<room_name>[\w-]+)/(?P<token>[\w\-\.]+)/$', consumers.CallConsumer.as_asgi()),
    re_path(r'^handle-call/(?P<room_name>\w+)/$', consumers.CallHandleConsumer.as_asgi()),
]
