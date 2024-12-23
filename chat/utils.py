from PIL import Image
import ffmpeg
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from threading import Thread
from django.utils import timezone
from datetime import timedelta
import requests
from .models import MessageNotification
from asgiref.sync import sync_to_async
from subscriptions.models import UserSubscription


def validate_image(file: UploadedFile):
    '''Validate that the image file is not corrupted.'''
    try:
        content_type = file.content_type
        if content_type not in ('image/png', 'image/jpeg', 'image/jpg'):
            return
        img = Image.open(file)
        img.verify()
        return True
    except Exception as err:
        print('Image validating error:', err)

def validate_video(file: UploadedFile):
    '''Validate that the video file is not corrupted.'''
    try:
        content_type = file.content_type
        if content_type not in ('video/mp4'):
            return
        probe = ffmpeg.probe(file.temporary_file_path())
        if 'streams' not in probe or len(probe['streams']) == 0:
            return
        return True
    except Exception as err:
        print('Video validating error:', err)

def push_notify(message):
    '''Send push notification'''
    notification_url = 'https://exp.host/--/api/v2/push/send'
    message = {
        'to': message.receiver.device_token,
        'sound': 'default',
        'title': message.sender.username,
        'body': message.content if message.msg_type == 'Text' else message.msg_type,
        'data': {}
    }
    response = requests.post(notification_url, json=message)
    if response.status_code == 200:
        print('Push notification sent successfully!')
    else:
        print('Failed to send push notification:')
        print('Response:', response.json())

@sync_to_async
def send_notification(user_message):
    '''
    Send chat message notification through email.
    
    Parameters:
    sender (str): Username of the person who sent the message.
    receiver_email (str): Email of the receiver.
    '''
    # Save notification
    try:
        MessageNotification.objects.create(sender=user_message.sender, receiver=user_message.receiver, message=user_message)
    except:
        pass

    # send push notification
    try:
        Thread(target=push_notify, args=(user_message,)).start()
    except:
        pass

    # send email notification
    subject = "You've Received a New Message on Metri Chat"
    message = f"""
    Hi there,

    You have a new message from {user_message.sender.username} on Metri Chat. 

    Log in to your account to view and respond to the message. 

    Here’s what you can do:
    - Continue your conversation with {user_message.sender.username}
    - Explore other messages and notifications

    Thank you for using Metri Chat! We hope you have a seamless and engaging communication experience.

    Best regards,
    Metri Bookshelf Team

    Note: Please do not reply to this email. This is an automated notification.
    """
    from_email = "Metribookshelf@gmail.com"
    recipient_list = [user_message.receiver.email]

    def send_email():
        send_mail(subject, message, from_email, recipient_list)

    try:
        Thread(target=send_email).start()
    except:
        pass

def time_since_last_login(last_login):
    if not last_login:
        return 'Few time ago'
    now = timezone.now()
    time_diff = now - last_login

    if time_diff < timedelta(minutes=1):
        return "Just now"
    elif time_diff < timedelta(hours=1):
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif time_diff < timedelta(days=1):
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif time_diff < timedelta(weeks=1):
        days = time_diff.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif time_diff < timedelta(days=30):
        weeks = time_diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif time_diff < timedelta(days=365):
        months = time_diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = time_diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


def msg_subscription_check(user):
    try:
        current_subscription = UserSubscription.objects.filter(user__username=user, active=True).first()

        if current_subscription:
            subscription_start_date = current_subscription.created_at
            subscription_duration = timedelta(days=current_subscription.subscription.time_period * 30)  # Convert months to days
            expiry_date = subscription_start_date + subscription_duration

            # Check if the subscription has expired
            if timezone.now() > expiry_date:
                # Deactivate the subscription
                current_subscription.delete()

                # Activate a new subscription if it exists
                new_subscription = UserSubscription.objects.filter(user__username=user).first()
                if new_subscription:
                    new_subscription.active = True
                    new_subscription.save()
                    current_subscription = new_subscription
                else:
                    return

        if not current_subscription:
            return

        if current_subscription.messages == 0:
            return

        if current_subscription.messages > 0:
            current_subscription.messages -= 1
            current_subscription.save()
            return True
    except Exception as er:
        print('Error:', er)
        return