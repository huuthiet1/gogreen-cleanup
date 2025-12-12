from django.utils import timezone
from .models import Notification

def send_notification(user, title, message, type='system'):
    """Tạo nhanh 1 thông báo cho người dùng"""
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        sent_at=timezone.now()
    )

import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import EmailOTP

def send_otp(email):
    otp = str(random.randint(100000, 999999))

    EmailOTP.objects.create(
        email=email,
        otp=otp,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    send_mail(
        subject="Mã đăng nhập WebGoGreen",
        message=f"Mã OTP của bạn là: {otp}\nCó hiệu lực trong 5 phút.",
        from_email=None,
        recipient_list=[email],
        fail_silently=False
    )
