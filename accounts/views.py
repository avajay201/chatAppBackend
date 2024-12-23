from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.db.models import Q
from .serializers import UserRegisterSerializer, UserProfileSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        device_token = request.data.get("device_token")
        
        user = User.objects.filter(Q(username=email) | Q(email=email)).first()
        if user and user.check_password(password):
            validated_data = {
                'username': user.username,
                'email': user.email,
                'password': password,
            }
            serializer = self.get_serializer(data=validated_data)
            serializer.is_valid(raise_exception=True)
            serializer.validated_data['username'] = user.username
            if device_token:
                user.device_token = device_token
                user.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
