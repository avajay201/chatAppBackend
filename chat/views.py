from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, F
from .models import Chat, Message, BlockedUser
from accounts.models import User
from .serializers import ChatSerializer, MessageSerializer, group_messages_by_date
from .utils import validate_image, validate_video


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user1 = request.data.get('user1')
        user2 = request.data.get('user2')

        if not user1 or not user2:
            return Response({'error': 'User not found!.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            participant1 = User.objects.get(username=user1)
            participant2 = User.objects.get(username=user2)
            if participant1.is_superuser or participant2.is_superuser:
                return Response({'error': 'Unable to create chat!.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User doesn\'t exist.'}, status=status.HTTP_404_NOT_FOUND)

        chat_name = f'{min(participant1.username, participant2.username)}__{max(participant1.username, participant2.username)}'

        chat, created = Chat.objects.get_or_create(name=chat_name)

        if created:
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_200_OK)
    
    def get(self, request):
        chats = Chat.objects.filter(name__contains=request.user.username).order_by(F('last_message__timestamp').desc(nulls_last=True))
        chat_serializer = ChatSerializer(chats, many=True, context={'user': request.user.username})
        return Response(chat_serializer.data, status=status.HTTP_200_OK)

class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        chat = request.data.get('chat')

        if not chat or '__' not in chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_poss1 = chat
        chat_poss2 = chat.split('__')[1] + '__' + chat.split('__')[0]

        chat = Chat.objects.filter(Q(name=chat_poss1) | Q(name=chat_poss2)).first()
        if not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        messages = Message.objects.filter(chat=chat).exclude(deleted_by=request.user).order_by('timestamp')
        message_serializer = MessageSerializer(messages, many=True)
        messages = group_messages_by_date(message_serializer.data)

        other_user = chat_poss1.split('__')[0] if request.user.username != chat_poss1.split('__')[0] else chat_poss1.split('__')[1]
        other_user = User.objects.filter(username=other_user).first()
        blocked = BlockedUser.objects.filter(user=other_user, blocked_user=request.user).first()
        other_blocked = BlockedUser.objects.filter(user=request.user, blocked_user=other_user).first()
        profile_data = {'blocked': True if blocked else False, 'other_blocked': True if other_blocked else False, 'profile_picture': other_user.profile_picture.url if other_user.profile_picture else None}
        return Response({'messages': messages, 'profile': profile_data}, status=status.HTTP_200_OK)

class MessageDelete(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        id = request.data.get('id')
        chat = request.data.get('name')
        if not id or not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_poss1 = chat
        chat_poss2 = chat.split('__')[1] + '__' + chat.split('__')[0]

        message = Message.objects.filter(id=id).first()
        if message.deleted_by and message.deleted_by == request.user:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if message.deleted_by:
            message.delete()
        else:
            message.deleted_by = request.user
            message.save()

        chat = Chat.objects.filter(Q(name=chat_poss1) | Q(name=chat_poss2)).first()
        if not message or not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        messages = Message.objects.filter(chat=chat).exclude(deleted_by=request.user).order_by('timestamp')
        if messages and not chat.last_message:
            chat.last_message = messages.last()
            chat.save()
        message_serializer = MessageSerializer(messages, many=True)
        messages = group_messages_by_date(message_serializer.data)
        return Response(messages, status=status.HTTP_200_OK)

class ChatClear(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        chat = request.data.get('name')
        if not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_poss1 = chat
        chat_poss2 = chat.split('__')[1] + '__' + chat.split('__')[0]

        chat = Chat.objects.filter(Q(name=chat_poss1) | Q(name=chat_poss2)).first()
        if not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        messages = Message.objects.filter(chat=chat).exclude(deleted_by=request.user)
        for message in messages:
            if message.deleted_by:
                message.delete()
            else:
                message.deleted_by = request.user
                message.save()
        return Response(status=status.HTTP_200_OK)

class BlockUser(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('user')
        block_status = request.data.get('status')

        if not block_status or not username or block_status not in ('block', 'unblock'):
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        if block_status == 'block':
            BlockedUser.objects.create(user=request.user, blocked_user=user)
        else:
            blocker = BlockedUser.objects.filter(user=request.user, blocked_user=user).first()
            if blocker:
                blocker.delete()
        return Response(status=status.HTTP_200_OK)

class MessageSend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data, '||', request.FILES, '||')
        msg_type = request.data.get('type')
        name = request.data.get('name')
        file = request.FILES.get('file')

        if not msg_type or not file or not name or msg_type not in ('image', 'video'):
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_poss1 = name
        chat_poss2 = name.split('__')[1] + '__' + name.split('__')[0]
        chat = Chat.objects.filter(Q(name=chat_poss1) | Q(name=chat_poss2)).first()
        if not chat:
            return Response({'error': 'Invalid request!.'}, status=status.HTTP_400_BAD_REQUEST)

        if msg_type == 'image':
            result = validate_image(file)
            if not result:
                return Response({'error': 'Invalid or corrupted image file!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            result = validate_video(file)
            print('result>>>', result)
            if not result:
                return Response({'error': 'Invalid or corrupted video file!'}, status=status.HTTP_400_BAD_REQUEST)

        receiver = chat.name.split('__')[1] if chat.name.split('__')[0] == request.user.username else chat.name.split('__')[0]
        receiver = User.objects.filter(username=receiver).first()
        if msg_type == 'image':
            message = Message.objects.create(chat=chat, msg_type='Image', image=file, sender=request.user, receiver=receiver)
        else:
            message = Message.objects.create(chat=chat, msg_type='Video', video=file, sender=request.user, receiver=receiver)
        chat.last_message = message
        chat.save()
        message_serializer = MessageSerializer(message)
        message = group_messages_by_date([message_serializer.data])
        message = message['Today'][0]
        return Response(message, status=status.HTTP_201_CREATED)
