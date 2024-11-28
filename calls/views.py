from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Call
from .serializers import CallSerializer
import firebase_admin
from firebase_admin import credentials, firestore
from accounts.models import User


cred = credentials.Certificate("/home/ameo/Pictures/chatAppBackend/metrichat-adb11-firebase-adminsdk-6wuid-6b766e39b2.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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
        user1 = request.data.caller
        user2 = request.data.receiver
        user1 = User.objects.filter(id=user1).first()
        user2 = User.objects.filter(id=user2).first()

        data = request.data
        data['caller'] = request.user.id
        serializer = CallSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()

            # delete firebase entry
            doc_ref = db.collection('meet').document('chatId')
            subcollections = doc_ref.collections()
            for subcollection in subcollections:
                if subcollection.id in [user1.username, user2.username]:
                    subcollection_ref = db.document('meet/chatId').collection(subcollection.id)
                    docs = subcollection_ref.stream()
                    for doc in docs:
                        subcollection_ref.document(doc.id).delete()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
