from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Call
from .serializers import CallSerializer
import firebase_admin
from firebase_admin import credentials, firestore
from accounts.models import User
from subscriptions.models import UserSubscription
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


cred = credentials.Certificate("<path>")
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
        calls = Call.objects.filter(Q(caller=request.user) | Q(receiver=request.user)).order_by('-call_time')  # Retrieve calls in descending order of time
        serializer = CallSerializer(calls, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new call record.
        """
        user1 = request.user.id
        user2 = request.data.get('receiver')
        call_duration = request.data.get('call_duration')
        user1 = User.objects.filter(id=user1).first()
        user2 = User.objects.filter(id=user2).first()

        data = request.data
        data['caller'] = request.user.id
        serializer = CallSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()

            # update subscription
            current_subscription = UserSubscription.objects.filter(user=request.user, active=True).first()
            if current_subscription:
                current_subscription.calls -= call_duration/60
                current_subscription.save()

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


class CallLimit(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_subscription = UserSubscription.objects.filter(user=request.user, active=True).first()

            if current_subscription:
                subscription_start_date = current_subscription.created_at
                subscription_duration = timedelta(days=current_subscription.subscription.time_period * 30)  # Convert months to days
                expiry_date = subscription_start_date + subscription_duration

                # Check if the subscription has expired
                if timezone.now() > expiry_date:
                    # Deactivate the subscription
                    current_subscription.delete()

                    # Activate a new subscription if it exists
                    new_subscription = UserSubscription.objects.filter(user=request.user).first()
                    if new_subscription:
                        new_subscription.active = True
                        new_subscription.save()
                        current_subscription = new_subscription
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST)
            
            if not current_subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if current_subscription.calls == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if current_subscription.messages > 0:
                current_subscription.messages -= 1
                current_subscription.save()
                return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
