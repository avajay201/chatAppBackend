from django.urls import path
from .views import CallAPIView

urlpatterns = [
    path('list-calls/', CallAPIView.as_view(), name='call-api'),
]
