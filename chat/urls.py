from django.urls import path
from .views import ChatView, MessageView, MessageDelete, ChatClear, BlockUser

urlpatterns = [
    path('chats/', ChatView.as_view(), name='chats'),
    path('messages/', MessageView.as_view(), name='messages'),
    path('message-delete/', MessageDelete.as_view(), name='message-delete'),
    path('clear-chat/', ChatClear.as_view(), name='clear-chat'),
    path('block-user/', BlockUser.as_view(), name='block-user'),
]
