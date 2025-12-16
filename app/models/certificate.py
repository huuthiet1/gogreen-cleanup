from django.db import models
from .user import User
from .event import Event

class ParticipationCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="certificates")
    file = models.FileField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_certificates")

    class Meta:
        db_table = "participation_certificates"
