from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from subscriptions.models import UserSubscription


User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True},
            'email': {'required': True}
        }

    def validate_password(self, value):
        if len(value) < 6 or len(value) > 20:
            raise ValidationError("Password must be between 6 and 20 characters.")
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'mobile_number', 'last_name', 'profile_picture', 'gender', 'dob', 'location', 'headline', 'about_me', 'caste', 'religion', 'height', 'weight', 'education', 'occupation', 'income', 'family_status', 'smoker', 'alcoholic', 'hobbies', 'skin_tone']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_id = request.user.id
            subscription = UserSubscription.objects.filter(user__id=user_id).first()
            representation['subscription'] = subscription.subscription.name if subscription else None
        else:
            representation['subscription'] = None

        return representation
