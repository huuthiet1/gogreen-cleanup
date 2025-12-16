from django.contrib import admin
from django.conf import settings
from django.core.mail import EmailMessage
from app.models import ParticipationCertificate

@admin.register(ParticipationCertificate)
class ParticipationCertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "approved", "created_at")
    list_filter = ("approved",)
    actions = ["send_certificate"]

    @admin.action(description="📧 Gửi giấy chứng nhận")
    def send_certificate(self, request, queryset):
        for cert in queryset:
            if cert.file and cert.user.email:
                email = EmailMessage(
                    subject="Giấy chứng nhận",
                    body="Đính kèm giấy chứng nhận của bạn.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[cert.user.email],
                )
                email.attach_file(cert.file.path)
                email.send(fail_silently=True)
