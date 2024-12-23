from rest_framework import serializers
from .models import Subscription, Addon, UserSubscription


class ApplyCouponSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField(required=True)
    coupon_code = serializers.CharField(max_length=50, required=True)
    addons = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,  # This field is optional
        allow_empty=True  # You can pass an empty list if no addons
    )

class AddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addon
        fields = ['id', 'type', 'messages', 'calls', 'price']

class SubscriptionSerializer(serializers.ModelSerializer):
    addons = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'name', 'price', 'description', 'time_period', 'messages', 'calls', 'addons']

    def get_addons(self, obj):
        addons = obj.addons.all()
        return AddonSerializer(addons, many=True).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_id = request.user.id
            subscription = UserSubscription.objects.filter(user__id=user_id, subscription=instance).first()
            representation['is_purchased'] = True if subscription else False
        else:
            representation['is_purchased'] = False

        return representation

class UserSubscriptionSerializer(serializers.ModelSerializer):
    addons = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = UserSubscription
        fields = '__all__'
    
    def create(self, validated_data):
        addon_ids = validated_data.pop('addons', [])

        user_subscription = UserSubscription.objects.create(**validated_data)

        if addon_ids:
            addons = Addon.objects.filter(id__in=addon_ids)
            user_subscription.addons.set(addons)

        return user_subscription
