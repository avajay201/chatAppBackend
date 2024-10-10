import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Message, Chat
from accounts.models import User
from django.db.models import Q, F
from .serializers import ConsumerMessageSerializer, MessageSerializer, ChatSerializer, group_messages_by_date


room_members = {}
class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None

    async def connect(self):
        r_name = self.scope['url_route']['kwargs']['room_name']
        auth_token = self.scope['url_route']['kwargs']['token']
        if not r_name or not auth_token:
            await self.close()

        try:
            authenticated = await self.authenticate(auth_token)
            if authenticated:
                user1, user2 = r_name.split('__')
                self.room_name = await self.users_exist(user1, user2)
                if self.room_name and (self.room_name not in room_members or len(room_members[self.room_name]) < 2):
                    await self.channel_layer.group_add(
                        self.room_name,
                        self.channel_name
                    )

                    await self.accept()
                    print('Room Name:', self.room_name)

                    if self.room_name in room_members:
                        room_members[self.room_name].add(self.channel_name)
                    else:
                        room_members[self.room_name] = set([self.channel_name])
                    messages = await self.update_messages(authenticated, user1, user2)
                    await self.channel_layer.group_send(
                        self.room_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'status': 'status', 
                                'result': 'online' if len(room_members[self.room_name]) == 2 else 'offline',
                                'messages': messages if len(room_members[self.room_name]) == 2 else None,
                            },
                        }
                    )
                else:
                    await self.close()
            else:
                await self.close()
        except Exception as er:
            print('Error:', er)
            await self.close()

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )
            if len(room_members[self.room_name]) > 1:
                room_members[self.room_name].discard(self.channel_name)
            else:
                del room_members[self.room_name]
            
            if self.room_name in room_members:
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'status': 'status', 
                            'result': 'online' if len(room_members[self.room_name]) == 2 else 'offline'
                        },
                    }
                )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_data = data.get('message')
        if not message_data:
            return
        status = message_data.get('status', '')
        print('Status:', status)
        if status == 'typing':
            try:
                receiver = message_data.get('receiver', '')
                receiver_channel_index = list(global_room_members.values()).index(receiver)
                receiver_channel = list(global_room_members.keys())[receiver_channel_index]

                await self.channel_layer.group_add(
                    'r_global',
                    self.channel_name
                )

                await self.channel_layer.send(
                    receiver_channel,
                    {
                        'type': 'group_message',
                        'message': message_data,
                    }
                )

                await self.channel_layer.group_discard(
                    'r_global',
                    self.channel_name
                )
            except Exception as er:
                print('Error:', er)

            if len(room_members[self.room_name]) == 1:
                return

            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat_message',
                    'message': message_data,
                }
            )
        elif status == 'msg':
            sender = message_data.get('sender', '')
            receiver = message_data.get('receiver', '')
            content = message_data.get('content', '')
            msg_type = message_data.get('type', '')
            try:
                message = await self.create_message(sender, receiver, content, msg_type)
                if not message:
                    return
                serailzed_message = ConsumerMessageSerializer(message)

                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'chat_message',
                        'message': {'status': 'msg', 'message': serailzed_message.data},
                    }
                )
            except Exception as err:
                print('Message save error:', err)

            if len(room_members[self.room_name]) == 1:
                # send_notification()
                chats = await self.user_chats(receiver)
                try:
                    receiver_channel_index = list(global_room_members.values()).index(receiver)
                    receiver_channel = list(global_room_members.keys())[receiver_channel_index]

                    await self.channel_layer.group_add(
                        'r_global',
                        self.channel_name
                    )

                    await self.channel_layer.send(
                        receiver_channel,
                        {
                            'type': 'group_message',
                            'message': {'status': 'msg', 'chats': chats},
                        }
                    )

                    await self.channel_layer.group_discard(
                        'r_global',
                        self.channel_name
                    )
                except Exception as er:
                    print('Error:', er)
        elif status == 'block':
            if len(room_members[self.room_name]) == 2:
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'chat_message',
                        'message': message_data,
                    }
                )
        elif status == 'media_update':
            if len(room_members[self.room_name]) == 2:
                updated = await self.message_seen_update(message_data['message']['id'])
                if updated:
                    message_data['message']['is_seen'] = True
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'chat_message',
                        'message': {'status': 'msg', 'message': message_data['message']},
                    }
                )

    async def chat_message(self, event):
        print('event>>>', event)
        await self.send(text_data=json.dumps({
            'message': event['message'],
        }))

    @database_sync_to_async
    def users_exist(self, username1, username2):
        users = User.objects.filter(username__in=[username1, username2]).count()
        chat = Chat.objects.filter(Q(name=f'{username1}__{username2}') | Q(name=f'{username2}__{username1}')).first()
        if users == 2 and chat:
            return chat.name

    @database_sync_to_async
    def authenticate(self, token):
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            return user.username
        except:
            return

    @database_sync_to_async
    def create_message(self, sender, receiver, content, msg_type):
        '''save new message into db'''
        chat = Chat.objects.filter(name=self.room_name).first()
        sender = User.objects.filter(username=sender).first()
        receiver = User.objects.filter(username=receiver).first()
        message = None
        if msg_type == 'text':
            message = Message.objects.create(chat=chat, sender=sender, receiver=receiver, content=content, msg_type='Text')
            if len(room_members[self.room_name]) == 2:
                message.is_seen = True
                message.save()
            chat.last_message = message
            chat.save()
        return message

    @database_sync_to_async
    def update_messages(self, auth_user, username1, username2):
        '''update unseen messages'''
        sender = username2 if auth_user == username1 else username1
        chat = Chat.objects.filter(name=self.room_name).first()
        messages = Message.objects.filter(sender__username=sender, receiver__username=auth_user, is_seen=False)
        if messages:
            messages.update(is_seen=True)
            messages = Message.objects.filter(chat=chat).order_by('timestamp')
            message_serializer = MessageSerializer(messages, many=True)
            messages = group_messages_by_date(message_serializer.data)
            return messages

    @database_sync_to_async
    def user_chats(self, user):
        '''Get user chats'''
        chats = Chat.objects.filter(name__contains=user).order_by(F('last_message__timestamp').desc(nulls_last=True))
        chat_serializer = ChatSerializer(chats, many=True, context={'user': user})
        return chat_serializer.data

    @database_sync_to_async
    def message_seen_update(self, msg_id):
        '''Update message seen'''
        message = Message.objects.filter(id=msg_id).first()
        if message:
            message.is_seen = True
            message.save()
            return True

    async def group_message(self, event):
        '''Temp handler for global consumer'''


global_room_members = {}
class GlobalConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = 'r_global'

    async def connect(self):
        auth_token = self.scope['url_route']['kwargs']['token']
        try:
            print('connecting...')
            authenticated = await self.authenticate(auth_token)
            print('authenticated>>>', authenticated, 'global_room_members??>>', global_room_members)
            if authenticated:
                # if user already exists in connections, remove that user's channel
                exists_channels = list(global_room_members.values())
                channel_index = exists_channels.index(authenticated) if authenticated in exists_channels else None
                if channel_index is not None:
                    channel = list(global_room_members.keys())[channel_index]
                    del global_room_members[channel]

                await self.channel_layer.group_add(
                    self.room_name,
                    self.channel_name
                )
                await self.accept()

                # add new channel in group
                global_room_members[self.channel_name] = authenticated

                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'group_message',
                        'message': {'status': 'status', 'members': list(global_room_members.values())},
                    }
                )
            else:
                self.close()
        except Exception as er:
            print('Global WS connection Error:', er)
            self.close()

    async def disconnect(self, close_code):
        if self.channel_name in global_room_members:
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )

            # remove this channel from group
            del global_room_members[self.channel_name]

            # inform to group that a user is disconnected from this group
            if global_room_members:
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'group_message',
                        'message': {'status': 'status', 'members': list(global_room_members.values())},
                    }
                )

    async def group_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def authenticate(self, token):
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            return user.username
        except Exception as err:
            print('Error:', err)
            return

# def send_notification():
#     '''Send chat message notification'''

call_room_members = {}
class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        r_name = self.scope['url_route']['kwargs']['room_name']
        auth_token = self.scope['url_route']['kwargs']['token']
        if not r_name or not auth_token:
            await self.close()
        
        try:
            authenticated = await self.authenticate(auth_token)
            if authenticated:
                user1, user2 = r_name.split('__')
                self.room_name = await self.users_exist(user1, user2)
                if self.room_name and (self.room_name not in call_room_members or len(call_room_members[self.room_name]) < 2):
                    await self.channel_layer.group_add(
                        self.room_name,
                        self.channel_name
                    )
                await self.accept()
            else:
                await self.close()
        except Exception as er:
            print('Error:', er)
            await self.close()

    async def disconnect(self, close_code):
        if self.room_name and self.room_name in call_room_members:
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )
            if len(call_room_members[self.room_name]) > 1:
                call_room_members[self.room_name].discard(self.channel_name)
            else:
                del call_room_members[self.room_name]

    async def receive(self, text_data):
        receive_dict = json.loads(text_data)
        action = receive_dict['action']

        if action == 'new-offer' or action == 'new-answer':
            print("receive_dict['message']>>>", receive_dict)
            receive_channel_name = receive_dict['message']['receive_channel_name']
            receive_dict['message']['receive_channel_name'] = self.channel_name

            await self.channel_layer.send(
            receive_channel_name,
                {
                    'type': 'call_message',
                    'receive_dict': receive_dict,
                }
            )

            return

        receive_dict['receive_channel_name'] = self.channel_name

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'call_message',
                'receive_dict': receive_dict,
            }
        )

    async def call_message(self, event):
        receive_dict = event['receive_dict']
        # print('Call msg received from client:', receive_dict)

        await self.send(text_data=json.dumps({
            'message': receive_dict
        }))

    @database_sync_to_async
    def authenticate(self, token):
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            return user.username
        except Exception as err:
            print('Error:', err)
            return
    
    @database_sync_to_async
    def users_exist(self, username1, username2):
        users = User.objects.filter(username__in=[username1, username2]).count()
        chat = Chat.objects.filter(Q(name=f'{username1}__{username2}') | Q(name=f'{username2}__{username1}')).first()
        if users == 2 and chat:
            return chat.name
