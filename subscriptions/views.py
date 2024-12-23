from rest_framework import generics
from .models import Subscription
from .serializers import SubscriptionSerializer, ApplyCouponSerializer, UserSubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .models import Subscription, Coupon, Addon, UserSubscription
import uuid
import hashlib
from bs4 import BeautifulSoup
import requests
from django.template.loader import render_to_string
from django.conf import settings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class SubscriptionListCreateView(generics.ListCreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ApplyCouponView(APIView):
    def post(self, request, *args, **kwargs):
        # Deserialize the incoming request data
        serializer = ApplyCouponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        subscription_id = serializer.validated_data['subscription_id']
        coupon_code = serializer.validated_data['coupon_code']
        addon_ids = serializer.validated_data.get('addons', [])  # Get addon ids if provided

        try:
            # Validate subscription
            subscription = Subscription.objects.get(id=subscription_id)
        except ObjectDoesNotExist:
            return Response({"error": "Invalid subscription ID."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Validate coupon
            coupon = Coupon.objects.get(code=coupon_code)
        except ObjectDoesNotExist:
            return Response({"error": "Invalid coupon code."}, status=status.HTTP_404_NOT_FOUND)

        if not coupon.is_valid():
            return Response({"error": "Coupon is not valid."}, status=status.HTTP_400_BAD_REQUEST)

        # Initial total price with the subscription price
        total_price = subscription.price

        # Add the price of each addon
        addon_discount_total = 0
        for addon_id in addon_ids:
            try:
                addon = Addon.objects.get(id=addon_id)
            except ObjectDoesNotExist:
                return Response({"error": f"Invalid addon ID: {addon_id}"}, status=status.HTTP_404_NOT_FOUND)

            # Add the price of the addon to the total price
            total_price += addon.price

        # Apply coupon discount on the total price
        original_total_price = total_price  # Save the original total price before applying the coupon
        discount = (original_total_price * coupon.discount) / 100

        # Ensure the discount doesn't reduce the price below zero
        final_price = max(0, original_total_price - discount)

        # Calculate the discount applied to the subscription and addons separately for clarity
        subscription_discount = (subscription.price * coupon.discount) / 100
        final_subscription_price = max(0, subscription.price - subscription_discount)

        # For addons, apply the same discount
        addon_discount_total = 0
        for addon_id in addon_ids:
            addon = Addon.objects.get(id=addon_id)
            addon_discount = (addon.price * coupon.discount) / 100
            addon_discount_total += addon_discount

        final_addon_price = 0
        for addon_id in addon_ids:
            addon = Addon.objects.get(id=addon_id)
            final_addon_price += max(0, addon.price - (addon.price * coupon.discount) / 100)

        # Return the response with both the subscription and addon prices
        return Response({
            "final_total_price": final_price,
            "coupon_code": coupon_code,
            "addons": addon_ids,
            "discount": coupon.discount,
        }, status=status.HTTP_200_OK)


class MakePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract subscription_id and user_id from query params
        subscription_id = request.data.get('subscription_id', None)
        price_param = request.data.get('price', None)

        if not subscription_id:
            return Response({"error": "subscription_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch subscription details
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

        unique_id = uuid.uuid4()

        # Convert UUID to a string
        unique_id_str = str(unique_id)
        print(unique_id_str)

        print(unique_id_str)
        api_key = "t108UM"
        salt = "dWwGvm4Bv5bEsQpZWVtheoJIZyYgZ68W"
        txn_id = unique_id_str
        amount = price_param
        product_info = subscription.description
        first_name = request.user.first_name
        email = request.user.email
        phone = request.user.mobile_number
        surl = "http://192.168.1.101:8000/payment-success/"
        furl = "http://192.168.1.101:8000/payment-failure/"

        # Create the hash string
        hash_string = f"{api_key}|{txn_id}|{amount}|{product_info}|{first_name}|{email}|||||||||||{salt}"
        hash = hashlib.sha512(hash_string.encode()).hexdigest()

        # Payment gateway URL
        url = "https://test.payu.in/_payment"

        # Prepare the payload for the request
        payload = {
            "key": api_key,
            "txnid": txn_id,
            "amount": price_param,
            "productinfo": product_info,
            "firstname": first_name,
            "email": email,
            "phone": phone,
            "surl": surl,
            "furl": furl,
            "hash": hash
        }

        # Send the request to the payment gateway with redirects disabled
        response = requests.post(url, data=payload, allow_redirects=False)

        # Capture the 'Location' header from the response
        redirect_url = response.headers.get('Location')

        # Check if the response status code is 302 (redirect)
        if response.status_code == 302 and redirect_url:
            # Return the redirect URL as part of the response
            return Response({"message": "Payment initiated", "redirect_url": redirect_url}, status=status.HTTP_200_OK)
        else:
            # Return error response if payment initiation failed
            return Response({"error": "Failed to initiate payment", "response": response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the payment_url and coupon from request data
        payment_url = request.data.get("payment_url")
        coupon = request.data.get("coupon")
        subscription = request.data.get("subscription_id")
        addons = request.data.get("addons")

        if not payment_url:
            return Response({"error": "Payment URL not provided"}, status=status.HTTP_400_BAD_REQUEST)

        response = requests.get(payment_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        form_tag = soup.find('form')

        if form_tag:
            try:
                # Extract necessary data from the form
                txn_id = form_tag.find('input', {'name': 'txnid'})['value']
                amount = form_tag.find('input', {'name': 'amount'})['value']
                mode = form_tag.find('input', {'name': 'mode'})['value']
                product_info = form_tag.find('input', {'name': 'productinfo'})['value']
                firstname = form_tag.find('input', {'name': 'firstname'})['value']
                email = form_tag.find('input', {'name': 'email'})['value']
                phone = form_tag.find('input', {'name': 'phone'})['value']
                payment_status = form_tag.find('input', {'name': 'status'})['value']
                mihpayid = form_tag.find('input', {'name': 'mihpayid'})['value']
                card_category = form_tag.find('input', {'name': 'cardCategory'})['value']
            except:
                return Response(status=status.HTTP_200_OK)

            # Process payment data
            payment_data = {
                'txn_id': txn_id,
                'mihpayid': mihpayid,
                'amount': amount,
                'mode': mode,
                'product_info': product_info,
                'firstname': firstname,
                'email': email,
                'phone': phone,
                'status': payment_status,
                'card_category': card_category,
                'coupon': coupon,
                'subscription': subscription,
                'addons': addons,
                'user': request.user.id,
            }

            serializer = UserSubscriptionSerializer(data=payment_data)

            if serializer.is_valid():
                serializer.save()
                if payment_status.lower() == "success":
                    msg = MIMEMultipart("related")
                    msg["Subject"] = "Your Payment Invoice"
                    msg["From"] = settings.EMAIL_HOST_USER
                    msg["To"] = email

                    subscription = Subscription.objects.filter(id=subscription).first()
                    addons = Addon.objects.filter(id__in=addons)

                    total_messages = subscription.messages + sum(addon.messages for addon in addons)
                    total_calls = subscription.calls + sum(addon.calls for addon in addons)
                    try:
                        total_subscription = UserSubscription.objects.filter(user=request.user).count()
                        user_subscription = UserSubscription.objects.filter(user=request.user, subscription=subscription).first()
                        user_subscription.messages = total_messages
                        user_subscription.calls = total_calls
                        if total_subscription > 1:
                            user_subscription.active = False
                        user_subscription.save()
                    except Exception as err:
                        print(err, '+++++++++++++')

                    html_content = render_to_string('payment_invoice_email.html', {
                        'txn_id': txn_id,
                        'amount': amount,
                        'mode': mode,
                        'subscription': subscription,
                        'firstname': firstname,
                        'email': email,
                        'phone': phone,
                        'mihpayid': mihpayid,
                        'card_category': card_category,
                        'coupon': coupon,
                        'addons': addons,
                    })

                    msg_html = MIMEText(html_content, "html")
                    msg.attach(msg_html)
                    couponObj = Coupon.objects.filter(code=coupon).first()
                    if couponObj:
                        couponObj.usage_count += 1
                        couponObj.save()

                    try:
                        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                            server.starttls()
                            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                            server.sendmail(settings.EMAIL_HOST_USER, email, msg.as_string())
                        print("Email sent successfully!")
                    except Exception as e:
                        print(f"Failed to send email: {e}")

                    return Response({"message": "Payment details saved and invoice sent successfully"}, status=status.HTTP_201_CREATED)
                else:
                    print('777777777777777777777777777777')
                    return Response({"error": "Payment failed, no invoice sent"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                print('++++++++++++++++++++++++', serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("No form tag found on this page.")
            return Response("No form tag found on this page.", status=status.HTTP_400_BAD_REQUEST)
