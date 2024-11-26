from accounts.models import User
from collections import defaultdict
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from .models import Chat, Message, BlockedUser, MessageNotification
import pytz
from rest_framework import serializers


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['last_message']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        current_user = self.context.get('user')

        participants = instance.name.split('__')
        participant1_username = participants[0]
        participant2_username = participants[1]

        if current_user == participant1_username:
            user = User.objects.get(username=participant2_username)
        else:
            user = User.objects.get(username=participant1_username)

        sender = participant2_username if current_user == participant1_username else participant1_username
        unseen_msgs = Message.objects.filter(sender__username=sender, receiver__username=current_user, is_seen=False).count()

        last_message = instance.last_message
        if last_message and last_message.deleted_by and last_message.deleted_by.username == current_user:
            last_message = Message.objects.filter(chat=instance).exclude(deleted_by__username=current_user).order_by('timestamp').last()

        is_blocked = BlockedUser.objects.filter(Q(user__username=user) & Q(blocked_user__username=current_user) | Q(user__username=current_user) & Q(blocked_user__username=user)).first()
        blocked = BlockedUser.objects.filter(user__username=user, blocked_user__username=current_user).first()
        if blocked:
            profile_pic = None
        else:
            profile_pic = user.profile_picture.url if user.profile_picture else None

        representation['id'] = instance.id
        representation['username'] = user.username
        representation['user_id'] = user.id
        representation['profile_picture'] = profile_pic
        representation['last_message'] = last_message.content if last_message else None
        representation['msg_type'] = last_message.msg_type if last_message else None
        representation['unseen_msgs'] = unseen_msgs
        representation['is_typing'] = False
        representation['is_blocked'] = True if is_blocked else False
        representation['blocked'] = True if blocked else False
        representation['last_message_time'] = format_message_time(last_message.timestamp, last_message_time=True) if last_message else None

        return representation

def format_message_time(timestamp, message_time=False, last_message_time=False):
    '''Format time using indian time'''
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_time = timestamp.astimezone(ist_timezone)

    if message_time:
        return ist_time.strftime('%I:%M %p') # Format as 12:15 PM

    current_time = timezone.now().astimezone(ist_timezone)

    
    if last_message_time:
        if ist_time.date() == current_time.date():
            return ist_time.strftime('%I:%M %p') # Format as 12:15 PM

        if ist_time.date() == (current_time - timedelta(days=1)).date():
            return "Yesterday"

        return ist_time.strftime('%-d %B, %Y') # Format as '5 October, 2024'

    if ist_time.date() == current_time.date():
        return "Today"

    if ist_time.date() == (current_time - timedelta(days=1)).date():
        return "Yesterday"

    return ist_time.strftime('%-d %B, %Y') # Format as '5 October, 2024'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('content', 'id', 'image', 'is_seen', 'msg_type', 'receiver', 'sender', 'timestamp', 'video')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sender'] = instance.sender.username
        representation['receiver'] = instance.receiver.username
        representation['timestamp'] = instance.timestamp
        return representation

class ConsumerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('content', 'id', 'image', 'is_seen', 'msg_type', 'receiver', 'sender', 'timestamp', 'video')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sender'] = instance.sender.username
        representation['receiver'] = instance.receiver.username
        representation['timestamp'] = format_message_time(instance.timestamp, True)
        return representation

def group_messages_by_date(messages):
    grouped_messages = defaultdict(list)

    for message in messages:
        timestamp = message['timestamp']
        date_key = format_message_time(timestamp)
        message['timestamp'] = format_message_time(timestamp, True)
        grouped_messages[date_key].append(message)

    return grouped_messages

class MessageNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageNotification
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sender'] = instance.sender.username
        representation['receiver'] = instance.receiver.username
        representation['timestamp'] = format_message_time(instance.timestamp, last_message_time=True)
        return representation
