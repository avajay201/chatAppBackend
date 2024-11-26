from django.db import models
from accounts.models import User


class Call(models.Model):
    CALL_TYPE_CHOICES = [
        ('Audio', 'Audio'),
        ('Video', 'Video'),
    ]

    call_type = models.CharField(
        max_length=10,
        choices=CALL_TYPE_CHOICES,
    )
    caller = models.ForeignKey(
        User,
        related_name='outgoing_calls',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User,
        related_name='incoming_calls',
        on_delete=models.CASCADE
    )
    call_duration = models.CharField(max_length=20)
    call_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.call_type} call from {self.caller.username} to {self.receiver.username} at {self.call_time}"