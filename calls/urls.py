from django.urls import path
from .views import CallAPIView, CallLimit

urlpatterns = [
    path('list-calls/', CallAPIView.as_view(), name='call-api'),
    path('call-limit/', CallLimit.as_view(), name='call-limit'),
]
