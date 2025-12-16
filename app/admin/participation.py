from django.db import models
from django.conf import settings
from .event import Event

class EventParticipation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    checkin_photo = models.JSONField(default=list, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verified_participants')
    verified_at = models.DateTimeField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'event_participation'
