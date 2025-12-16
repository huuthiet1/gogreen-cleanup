from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string

class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Sắp diễn ra'),
        ('in_progress', 'Đang diễn ra'),
        ('done', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    points = models.IntegerField(default=0)
    datetime_start = models.DateTimeField(default=timezone.now)
    datetime_end = models.DateTimeField(default=timezone.now)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    participants_max = models.IntegerField(default=0)
    participants_current = models.IntegerField(default=0)

    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    qr_code_id = models.CharField(max_length=50, unique=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_otp(self):
        self.otp_code = get_random_string(6, '0123456789')
        self.otp_expires_at = self.datetime_end
        self.save()

    class Meta:
        db_table = 'events'
