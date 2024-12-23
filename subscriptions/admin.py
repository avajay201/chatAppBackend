from django.contrib import admin
from .models import Addon, Coupon, Subscription, UserSubscription

admin.site.register(Addon)
admin.site.register(Coupon)
admin.site.register(Subscription)
admin.site.register(UserSubscription)
