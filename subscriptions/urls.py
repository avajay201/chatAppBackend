from django.urls import path
from .views import SubscriptionListCreateView, ApplyCouponView, MakePaymentView, PaymentCreate

urlpatterns = [
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('make-payment/', MakePaymentView.as_view(), name='make_payment'),
    path('payment-create/', PaymentCreate.as_view(), name='make_payment'),
]
