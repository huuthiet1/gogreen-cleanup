from django.db import models
from django.conf import settings

class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge_name = models.CharField(max_length=100)
    badge_icon = models.CharField(max_length=255, null=True, blank=True)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_badges'
