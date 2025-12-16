from django.db import models
from django.utils import timezone
from django.conf import settings
from .event import Event

class Checkin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verified_checkins')
    verified_at = models.DateTimeField(null=True, blank=True)
    otp_used = models.CharField(max_length=6, null=True, blank=True)

    class Meta:
        db_table = 'checkins'
