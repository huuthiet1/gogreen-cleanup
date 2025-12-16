from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from app.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "preview_image",
        "predicted_trash_type", "estimated_weight_ton",
        "recommended_volunteers", "admin_status", "created_at"
    )
    list_filter = ("admin_status", "predicted_trash_type")
    readonly_fields = (
        "preview_image", "analysis_summary",
        "predicted_trash_type", "estimated_weight_ton",
        "recommended_volunteers", "created_at", "verified_at"
    )
    actions = ["approve_and_notify"]

    def preview_image(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="120"/>', obj.images.url)
        return "—"

    @admin.action(description="✅ Duyệt & gửi email")
    def approve_and_notify(self, request, queryset):
        for report in queryset:
            if report.admin_status == "approved":
                continue
            report.admin_status = "approved"
            report.verified_at = timezone.now()
            report.save()

            if report.user.email:
                EmailMessage(
                    subject="Báo cáo đã được duyệt",
                    body=f"Chào {report.user.username}, báo cáo của bạn đã được duyệt.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[report.user.email],
                ).send(fail_silently=True)
