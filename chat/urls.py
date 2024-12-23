from django.urls import path
from .views import ChatView, MessageView, MessageSend, MessageDelete, ChatClear, BlockUser, ReportUser, Notifications, RoomCreate

urlpatterns = [
    path('chats/', ChatView.as_view(), name='chats'),
    path('messages/', MessageView.as_view(), name='messages'),
    path('send-message/', MessageSend.as_view(), name='send-message'),
    path('message-delete/', MessageDelete.as_view(), name='message-delete'),
    path('clear-chat/', ChatClear.as_view(), name='clear-chat'),
    path('block-user/', BlockUser.as_view(), name='block-user'),
    path('report-user/', ReportUser.as_view(), name='report-user'),
    path('notifications/', Notifications.as_view(), name='notifications'),
    path('room-create/', RoomCreate.as_view(), name='room-create'),
]
