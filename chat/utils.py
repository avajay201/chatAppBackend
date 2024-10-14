from PIL import Image
import ffmpeg
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from threading import Thread
from django.utils import timezone
from datetime import timedelta


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
        print('content_type>>>', content_type)
        if content_type not in ('video/mp4'):
            return
        probe = ffmpeg.probe(file.temporary_file_path())
        if 'streams' not in probe or len(probe['streams']) == 0:
            return
        return True
    except Exception as err:
        print('Video validating error:', err)

def send_notification(sender, receiver_email):
    '''
    Send chat message notification through email.
    
    Parameters:
    sender (str): Username of the person who sent the message.
    receiver_email (str): Email of the receiver.
    '''
    subject = "You've Received a New Message on Metri Chat"
    message = f"""
    Hi there,

    You have a new message from {sender} on Metri Chat. 

    Log in to your account to view and respond to the message. 

    Here’s what you can do:
    - Continue your conversation with {sender}
    - Explore other messages and notifications

    Thank you for using Metri Chat! We hope you have a seamless and engaging communication experience.

    Best regards,
    Metri Bookshelf Team

    Note: Please do not reply to this email. This is an automated notification.
    """
    from_email = "Metribookshelf@gmail.com"
    recipient_list = [receiver_email]

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
