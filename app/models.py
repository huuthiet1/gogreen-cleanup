from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.crypto import get_random_string
import uuid

from colorfield.fields import ColorField
# ==============================
# 1️⃣ NGƯỜI DÙNG (Custom User Model)
# ==============================
class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Tình nguyện viên'),
        ('admin', 'Quản trị viên'),
    ]

    phone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    points = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Danh sách người dùng'


# ==============================
# 2️⃣ SỰ KIỆN
# ==============================
class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Sắp diễn ra'),
        ('in_progress', 'Đang diễn ra'),
        ('done', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    points = models.IntegerField(default=0)
    datetime_start = models.DateTimeField(default=timezone.now)
    datetime_end = models.DateTimeField(default=timezone.now)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    participants_max = models.IntegerField(default=0)
    participants_current = models.IntegerField(default=0)

    # 🔐 MÃ OTP ĐIỂM DANH
    otp_code = models.CharField(max_length=6, null=True, blank=True, help_text="Mã OTP dùng để điểm danh sự kiện.")
    otp_expires_at = models.DateTimeField(null=True, blank=True, help_text="Thời gian hết hạn mã OTP.")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    qr_code_id = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 🧩 Sinh mã OTP khi tạo sự kiện (6 chữ số)
    def generate_otp(self):
        self.otp_code = get_random_string(length=6, allowed_chars='0123456789')
        self.otp_expires_at = self.datetime_end  # Hết hạn khi sự kiện kết thúc
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'events'
        verbose_name = 'Sự kiện'
        verbose_name_plural = 'Danh sách sự kiện'


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_images')
    image = models.ImageField(upload_to='events/')

    def __str__(self):
        return f"Ảnh của {self.event.title}"


from django.conf import settings
from django.db import models


class Report(models.Model):

    # ===== LOẠI RÁC (KEY KHÔNG DẤU – LABEL CÓ DẤU) =====
    class TrashType(models.TextChoices):
        NHUA = "nhua", "Nhựa"
        KIM_LOAI = "kim_loai", "Kim loại"
        HUU_CO = "huu_co", "Hữu cơ"
        KHAC = "khac", "Khác"

    # ===== TRẠNG THÁI ADMIN =====
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã chấp nhận"
        REJECTED = "rejected", "Từ chối"

    # ===== USER =====
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    description = models.TextField(null=True, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Địa chỉ suy ra từ GPS",
    )

    # MVP: 1 ảnh
    images = models.ImageField(
        upload_to="report_images/",
        null=True,
        blank=True,
    )

    # ===== AI RESULT =====
    predicted_trash_type = models.CharField(
        max_length=20,
        choices=TrashType.choices,
        null=True,
        blank=True,
        help_text="Loại rác chính do AI dự đoán",
    )

    estimated_weight_ton = models.FloatField(
        default=0,
        help_text="Khối lượng rác ước tính (tấn)",
    )

    recommended_volunteers = models.PositiveIntegerField(
        default=0,
        help_text="Số tình nguyện viên gợi ý",
    )

    analysis_summary = models.TextField(
        null=True,
        blank=True,
        help_text="Báo cáo phân tích AI",
    )

    # ===== ADMIN =====
    admin_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    # ===== TIME =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report #{self.id}"

    class Meta:
        db_table = "reports"
        verbose_name = "Gợi ý điểm rác"
        verbose_name_plural = "Danh sách điểm rác"



# ==============================
# 4️⃣ CHECK-IN (Điểm danh bằng OTP)
# ==============================
class Checkin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verified_checkins')
    verified_at = models.DateTimeField(null=True, blank=True)
    otp_used = models.CharField(max_length=6, null=True, blank=True, help_text="Mã OTP được dùng để check-in.")

    # 🧩 Xác nhận check-in bằng mã OTP
    @classmethod
    def verify_by_otp(cls, user, otp):
        event = Event.objects.filter(otp_code=otp).first()
        now = timezone.now()

        if not event:
            return None, "❌ Mã OTP không hợp lệ."
        if not (event.datetime_start <= now <= event.datetime_end):
            return None, "⚠️ Mã OTP chưa đến giờ hoặc đã hết hạn."
        if cls.objects.filter(user=user, event=event).exists():
            return None, "✅ Bạn đã điểm danh sự kiện này rồi."

        checkin = cls.objects.create(user=user, event=event, verified=True, otp_used=otp)
        user.points += event.points
        user.save()
        return checkin, f"🎉 Điểm danh thành công! Bạn được +{event.points} điểm 🌱"

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    class Meta:
        db_table = 'checkins'
        verbose_name = 'Check-in'
        verbose_name_plural = 'Lịch sử check-in'


# ==============================
# 5️⃣ NGƯỜI THAM GIA SỰ KIỆN
# ==============================
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

    def __str__(self):
        return f"{self.user.username} tham gia {self.event.title}"

    class Meta:
        db_table = 'event_participation'
        verbose_name = 'Người tham gia sự kiện'
        verbose_name_plural = 'Danh sách người tham gia'


# ==============================
# 6️⃣ PHẦN THƯỞNG
# ==============================
class Reward(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    required_points = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'rewards'
        verbose_name = 'Phần thưởng'
        verbose_name_plural = 'Danh sách phần thưởng'


# ==============================
# 7️⃣ LỊCH SỬ ĐỔI QUÀ
# ==============================
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

    def __str__(self):
        return f"{self.user.username} đổi {self.reward.title}"

    class Meta:
        db_table = 'reward_redeem'
        verbose_name = 'Đổi quà'
        verbose_name_plural = 'Lịch sử đổi quà'


# ==============================
# 8️⃣ THÔNG BÁO
# ==============================
class Notification(models.Model):
    TYPE_CHOICES = [
        ('reminder', 'Nhắc lịch'),
        ('event', 'Sự kiện'),
        ('reward', 'Phần thưởng'),
        ('system', 'Hệ thống'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    related_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} → {self.user.username}"

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Danh sách thông báo'


# ==============================
# 9️⃣ BÌNH LUẬN SỰ KIỆN
# ==============================
class EventComment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bình luận sự kiện {self.event.title}"

    class Meta:
        db_table = 'event_comments'
        verbose_name = 'Bình luận sự kiện'
        verbose_name_plural = 'Danh sách bình luận'


# ==============================
# 🔟 NHẬT KÝ HỆ THỐNG
# ==============================
class ActivityLog(models.Model):
    ACTIONS = [
        ('create', 'Tạo'),
        ('update', 'Cập nhật'),
        ('delete', 'Xóa'),
        ('login', 'Đăng nhập'),
        ('system', 'Hệ thống'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=20, choices=ACTIONS, default='system')
    description = models.TextField()
    related_table = models.CharField(max_length=100, null=True, blank=True)
    related_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.action_type}] {self.description}"

    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Nhật ký hệ thống'
        verbose_name_plural = 'Lịch sử hành động'


# ==============================
# 1️⃣1️⃣ HUY HIỆU NGƯỜI DÙNG
# ==============================
class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge_name = models.CharField(max_length=100)
    badge_icon = models.CharField(max_length=255, null=True, blank=True)
    achieved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} đạt huy hiệu {self.badge_name}"

    class Meta:
        db_table = 'user_badges'
        verbose_name = 'Huy hiệu'
        verbose_name_plural = 'Danh sách huy hiệu'


# ==============================
# 1️⃣2️⃣ TIN NHẮN CHATBOT
# ==============================
class Message(models.Model):
    MESSAGE_TYPES = [
        ('user', 'Người dùng'),
        ('bot', 'Hệ thống / Bot'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages')
    content = models.TextField()
    is_from_bot = models.BooleanField(default=False)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='user')  # ✅ Thêm dòng này
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username}"

    class Meta:
        
        verbose_name = 'Tin nhắn'
        verbose_name_plural = 'Tin nhắn Chatbot/Admin'



# ==============================
# 1️⃣3️⃣ DANH MỤC PHÂN LOẠI RÁC (AI)
# ==============================
class TrashCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    sample_image = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'trash_categories'
        verbose_name = 'Danh mục rác'
        verbose_name_plural = 'Phân loại rác (AI)'

# ==============================
# 🔔 HÀM TIỆN ÍCH GỬI THÔNG BÁO
# ==============================

def send_notification(user, title, message, type='system'):
    """Tạo nhanh một thông báo cho người dùng"""
    from .models import Notification
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        sent_at=timezone.now()
    )


# ==============================
# 1️⃣4️⃣ MẠNG XÃ HỘI (BẠN BÈ & BÀI VIẾT)
# ==============================
class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, default='')
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True, default='')

    points = models.PositiveIntegerField(default=0, help_text="Điểm xanh của người dùng")
    health_score = models.PositiveIntegerField(default=100, help_text="Điểm sức khỏe môi trường")

    def __str__(self):
        return self.user.username


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images')
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    no_of_likes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.caption[:30]}"


class LikePost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


class Followers(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")

    def __str__(self):
        return f"{self.follower.username} → {self.user.username}"
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='comments/', blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bình luận {self.post.id}"
# ==============================
# 15️⃣ GIẤY CHỨNG NHẬN THAM GIA SỰ KIỆN
# ==============================
class ParticipationCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="certificates")
    file = models.FileField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_certificates"
    )

    class Meta:
        db_table = "participation_certificates"
        verbose_name = "Giấy chứng nhận"
        verbose_name_plural = "Danh sách giấy chứng nhận"

    def __str__(self):
        return f"Certificate {self.id} - {self.user.username} - {self.event.title}"


from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at