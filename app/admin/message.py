from django.db import models
from django.conf import settings

class Message(models.Model):
    MESSAGE_TYPES = [
        ('user', 'Người dùng'),
        ('bot', 'Hệ thống / Bot'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages')
    content = models.TextField()
    is_from_bot = models.BooleanField(default=False)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='user')
    sent_at = models.DateTimeField(auto_now_add=True)
