from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from app.models import Event, EventImage, Checkin, EventParticipation

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ("image", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100"/>', obj.image.url)
        return "—"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title", "status", "points", "datetime_start",
        "participants_current", "otp_colored"
    )
    readonly_fields = ("otp_code", "otp_expires_at", "created_at", "updated_at")
    list_filter = ("status",)
    inlines = [EventImageInline]
    actions = ["generate_otp_action"]

    def otp_colored(self, obj):
        if obj.otp_code:
            valid = not obj.otp_expires_at or obj.otp_expires_at > timezone.now()
            color = "#28a745" if valid else "#888"
            return format_html("<b style='color:{}'>{}</b>", color, obj.otp_code)
        return "—"

    @admin.action(description="🔐 Sinh OTP")
    def generate_otp_action(self, request, queryset):
        for event in queryset:
            event.generate_otp()

@admin.register(Checkin)
class CheckinAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "timestamp", "verified")

@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "joined_at", "verified", "points_awarded")
