from django.db import models

class Reward(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    required_points = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rewards'
