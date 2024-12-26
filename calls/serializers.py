from rest_framework import serializers
from chat.serializers import format_message_time
from .models import Call

class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['profile_picture'] = instance.receiver.profile_picture.url if instance.receiver.profile_picture else None
        representation['caller'] = instance.caller.username
        representation['caller_id'] = instance.caller.id
        representation['receiver'] = instance.receiver.username
        representation['receiver_id'] = instance.receiver.id
        representation['call_time'] = format_message_time(instance.call_time)
        return representation
