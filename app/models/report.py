from django.db import models
from django.conf import settings

class Report(models.Model):
    class TrashType(models.TextChoices):
        NHUA = "nhua", "Nhựa"
        KIM_LOAI = "kim_loai", "Kim loại"
        HUU_CO = "huu_co", "Hữu cơ"
        KHAC = "khac", "Khác"

    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã chấp nhận"
        REJECTED = "rejected", "Từ chối"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    description = models.TextField(null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    images = models.ImageField(upload_to="report_images/", null=True, blank=True)

    predicted_trash_type = models.CharField(max_length=20, choices=TrashType.choices, null=True, blank=True)
    estimated_weight_ton = models.FloatField(default=0)
    recommended_volunteers = models.PositiveIntegerField(default=0)
    analysis_summary = models.TextField(null=True, blank=True)

    admin_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"
