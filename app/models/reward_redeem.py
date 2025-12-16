from django.db import models
from django.conf import settings
from .reward import Reward

class RewardRedeem(models.Model):
    STATUS = [
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
        ('delivered', 'Đã giao'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    points_spent = models.IntegerField(default=0)
    quantity = models.IntegerField(default=1)
    redeem_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'reward_redeem'
