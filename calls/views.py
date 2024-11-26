from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Call
from .serializers import CallSerializer

class CallAPIView(APIView):
    """
    API for listing all calls and creating new calls.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve all call records.
        """
        calls = Call.objects.all().order_by('-call_time')  # Retrieve calls in descending order of time
        serializer = CallSerializer(calls, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new call record.
        """
        data = request.data
        data['caller'] = request.user.id  # Automatically set the authenticated user as the caller
        serializer = CallSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
