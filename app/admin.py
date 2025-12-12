from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import *
from django.core.mail import EmailMessage
from django.contrib.admin import AdminSite
from django.db.models import Count, Sum
from app.models import User, Event, EventParticipation, Report, RewardRedeem

# ========================
# 🧍 NGƯỜI DÙNG
# ========================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone", "role", "points", "is_active")
    search_fields = ("username", "email", "phone")
    list_filter = ("role", "is_active")
    readonly_fields = ("date_joined", "last_login")

    def has_add_permission(self, request):
        return True


# ========================
# 🖼 ẢNH SỰ KIỆN
# ========================
class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ("image", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;"/>', obj.image.url)
        return "—"
    preview.short_description = "Xem trước ảnh"

    verbose_name = "Ảnh sự kiện"
    verbose_name_plural = "Danh sách ảnh"


# ========================
# 🎯 SỰ KIỆN
# ========================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "points", "datetime_start",
                    "participants_current", "otp_colored", "otp_expires_at")
    search_fields = ("title", "address")
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at", "otp_code", "otp_expires_at")
    inlines = [EventImageInline]

    fieldsets = (
        ("🧾 Thông tin chung", {
            "fields": ("title", "description", "details", "points", "status")
        }),
        ("🕒 Thời gian & Địa điểm", {
            "fields": ("datetime_start", "datetime_end", "lat", "lng", "address")
        }),
        ("📞 Liên hệ & Quản lý", {
            "fields": ("participants_max", "participants_current",
                       "contact_phone", "qr_code_id", "created_by")
        }),
        ("🔐 Mã OTP điểm danh", {
            "fields": ("otp_code", "otp_expires_at"),
            "description": "Mã OTP sẽ được sinh tự động khi chọn hành động Sinh OTP."
        }),
    )

    actions = ["generate_otp_action"]

    def otp_colored(self, obj):
        """Hiển thị mã OTP màu xanh nếu còn hiệu lực, xám nếu hết hạn."""
        if obj.otp_code:
            color = "#28a745" if (not obj.otp_expires_at or obj.otp_expires_at > timezone.now()) else "#888"
            return format_html(f"<b style='color:{color}; font-size:14px;'>{obj.otp_code}</b>")
        return format_html("<span style='color:#ccc;'>—</span>")
    otp_colored.short_description = "Mã OTP"

    def generate_otp_action(self, request, queryset):
        count = 0
        for event in queryset:
            event.generate_otp()
            count += 1
        self.message_user(request, f"✅ Đã sinh mã OTP cho {count} sự kiện.")
    generate_otp_action.short_description = "🔐 Sinh mã OTP cho sự kiện được chọn"


# ========================
# 🧾 BÁO CÁO GỢI Ý ĐIỂM RÁC (AI)
# ========================
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "preview_image",
        "predicted_trash_type",
        "estimated_weight_ton",
        "recommended_volunteers",
        "admin_status",
        "created_at",
    )

    list_filter = ("admin_status", "predicted_trash_type")
    search_fields = ("user__username", "description", "address")

    readonly_fields = (
        "preview_image",
        "analysis_summary",
        "predicted_trash_type",
        "estimated_weight_ton",
        "recommended_volunteers",
        "lat",
        "lng",
        "address",
        "created_at",
        "verified_at",
    )

    fieldsets = (
        ("📸 Hình ảnh", {
            "fields": ("images", "preview_image")
        }),
        ("👤 Người gửi", {
            "fields": ("user",),
        }),
        ("📍 Vị trí", {
            "fields": ("lat", "lng", "address")
        }),
        ("🧠 Kết quả AI", {
            "fields": (
                "predicted_trash_type",
                "estimated_weight_ton",
                "recommended_volunteers",
                "analysis_summary",
            ),
        }),
        ("📌 Xử lý của Admin", {
            "fields": (
                "admin_status",
                "admin_check_location",
                "verified_at",
            ),
        }),
        ("🕒 Thời gian", {
            "fields": ("created_at",),
        }),
    )

    actions = ["approve_and_notify"]

    # =========================
    # 📧 ACTION: DUYỆT + GỬI EMAIL
    # =========================
    @admin.action(description="✅ Duyệt báo cáo & gửi email cho user")
    def approve_and_notify(self, request, queryset):
        count = 0

        for report in queryset:
            if report.admin_status == "approved":
                continue

            report.admin_status = "approved"
            report.verified_at = timezone.now()
            report.save(update_fields=["admin_status", "verified_at"])

            # Gửi email cho user
            if report.user.email:
                EmailMessage(
                    subject="📌 Báo cáo điểm rác của bạn đã được xác minh",
                    body=(
                        f"Xin chào {report.user.username},\n\n"
                        "Báo cáo điểm rác bạn gửi đã được đội ngũ quản trị xác minh.\n\n"
                        f"📍 Vị trí: {report.address or 'Không xác định'}\n"
                        f"🗑 Loại rác chính: {report.predicted_trash_type}\n"
                        f"⚖ Khối lượng ước tính: {report.estimated_weight_ton} tấn\n"
                        f"👥 Nhân lực đề xuất: {report.recommended_volunteers} người\n\n"
                        "Cảm ơn bạn đã chung tay bảo vệ môi trường 🌱\n\n"
                        "Trân trọng,\n"
                        "GoGreen System"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[report.user.email],
                ).send(fail_silently=True)

            count += 1

        self.message_user(
            request,
            f"✔ Đã duyệt & gửi email cho {count} báo cáo."
        )

    def preview_image(self, obj):
        if obj.images:
            return format_html(
                '<img src="{}" width="120" style="border-radius:8px; border:1px solid #ddd;" />',
                obj.images.url
            )
        return "Không có ảnh"

    preview_image.short_description = "Ảnh gửi"


# ========================
# 🕒 CHECK-IN
# ========================
@admin.register(Checkin)
class CheckinAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "timestamp", "verified", "verified_by")
    list_filter = ("verified",)
    search_fields = ("user__username", "event__title")


# ========================
# 👥 NGƯỜI THAM GIA
# ========================
@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "joined_at", "verified", "points_awarded")
    list_filter = ("verified",)
    search_fields = ("user__username", "event__title")


# ========================
# 🎁 PHẦN THƯỞNG
# ========================
@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("preview_image", "title", "required_points", "stock", "created_at")
    search_fields = ("title",)
    list_filter = ("created_at",)
    readonly_fields = ("preview_image",)

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="border-radius:8px;"/>', obj.image.url)
        return "—"
    preview_image.short_description = "Ảnh"


# ========================
# 💚 ĐỔI QUÀ
# ========================
@admin.register(RewardRedeem)
class RewardRedeemAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "points_spent", "status", "redeem_date")
    list_filter = ("status",)
    search_fields = ("user__username", "reward__title")


# ========================
# 🔔 THÔNG BÁO
# ========================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "type", "is_read", "sent_at")
    list_filter = ("type", "is_read")
    search_fields = ("user__username", "title")


# ========================
# 💬 BÌNH LUẬN SỰ KIỆN
# ========================
@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "created_at")
    search_fields = ("event__title", "user__username")


# ========================
# 📜 NHẬT KÝ HOẠT ĐỘNG
# ========================
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "description", "created_at")
    list_filter = ("action_type",)
    search_fields = ("user__username", "description")


# ========================
# 🏅 HUY HIỆU NGƯỜI DÙNG
# ========================
@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge_name", "achieved_at")
    search_fields = ("user__username", "badge_name")


# ========================
# 💌 TIN NHẮN CHATBOT
# ========================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "is_from_bot", "sent_at")
    search_fields = ("sender__username", "receiver__username", "content")


# ========================
# 🗑️ PHÂN LOẠI RÁC (AI)
# ========================
@admin.register(TrashCategory)
class TrashCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


# ================================
# 🌿 MẠNG XÃ HỘI
# ================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'health_score', 'location', 'bio')
    search_fields = ('user__username', 'location')
    list_filter = ('location',)



@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('preview_image', 'user', 'caption', 'created_at', 'no_of_likes')
    search_fields = ('user__username', 'caption')
    list_filter = ('created_at',)
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:8px;"/>', obj.image.url)
        return "—"
    preview_image.short_description = "Ảnh bài đăng"


@admin.register(LikePost)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post')
    search_fields = ('user__username', 'post__caption')


@admin.register(Followers)
class FollowersAdmin(admin.ModelAdmin):
    list_display = ('follower', 'user')
    search_fields = ('follower', 'user')




@admin.register(ParticipationCertificate)
class ParticipationCertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("user__username", "event__title")

    # 🌟 Chỉ còn 1 action duy nhất
    actions = ["send_certificate_email"]

    @admin.action(description="📧 Gửi giấy chứng nhận qua email")
    def send_certificate_email(self, request, queryset):
        sent_count = 0

        for cert in queryset:
            if not cert.file:
                continue  # Không có file PDF thì bỏ qua

            user_email = cert.user.email
            if not user_email:
                continue

            # Chuẩn bị email
            email = EmailMessage(
                subject="🌿 Giấy chứng nhận tham gia sự kiện GoGreen Cleanup",
                body=(
                    f"Xin chào {cert.user.username},\n\n"
                    f"Đính kèm là giấy chứng nhận tham gia hoạt động '{cert.event.title}'.\n"
                    f"Cảm ơn bạn đã chung tay vì môi trường xanh! 🌱\n\n"
                    f"Trân trọng,\nGoGreen Cleanup"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )

            # Gửi file PDF đính kèm
            email.attach(
                filename=cert.file.name.split("/")[-1],
                content=cert.file.read(),
                mimetype="application/pdf"
            )

            try:
                email.send()
                sent_count += 1
            except Exception as e:
                self.message_user(request, f"Lỗi gửi email tới {user_email}: {e}", level="error")

        self.message_user(request, f"📨 Đã gửi email cho {sent_count} người.")
