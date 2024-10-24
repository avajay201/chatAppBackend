from django.db import models
from accounts.models import User


MSG_TYPES = (
    ('Text', 'Text'),
    ('Image', 'Image'),
    ('Video', 'Video'),
)
class Message(models.Model):
    chat = models.ForeignKey('Chat', related_name='chats', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(null=True, blank=True, upload_to='chats/images')
    video = models.FileField(upload_to='chats/videos/', blank=True, null=True)
    sender = models.ForeignKey(User, related_name='sent_messages', null=True, on_delete=models.SET_NULL)
    receiver = models.ForeignKey(User, related_name='received_messages', null=True, on_delete=models.SET_NULL)
    msg_type = models.CharField(max_length=5, choices=MSG_TYPES)
    is_seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'Message from {self.sender.username} to {self.receiver.username}'

class Chat(models.Model):
    name = models.CharField(max_length=200, unique=True)
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='last_message_in_chat')

    def __str__(self):
        participants = self.name.split('__')
        return f'Chat between {participants[0]} and {participants[1]}'

class BlockedUser(models.Model):
    user = models.ForeignKey(User, related_name='blocker', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(User, related_name='blocked', on_delete=models.CASCADE)
    blocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} blocked {self.blocked_user}'

REASON_CHOICES = [
    ('spam', 'Spam'),
    ('harassment', 'Harassment'),
    ('offensive', 'Offensive Content'),
]
class Report(models.Model):
    user = models.ForeignKey(User, related_name='reports_made', on_delete=models.CASCADE)
    reported_user = models.ForeignKey(User, related_name='reports_received', on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} reported {self.reported_user} for {self.reason}'

class MessageNotification(models.Model):
    sender = models.ForeignKey(User, related_name='sent_notification', null=True, on_delete=models.SET_NULL)
    receiver = models.ForeignKey(User, related_name='received_notification', null=True, on_delete=models.SET_NULL)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_notification')
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
