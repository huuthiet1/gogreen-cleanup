# ===================================
# 📦 IMPORTS
# ===================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
# PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from django.db.models import Sum
# Forms
from .forms import ProfileUpdateForm

# Utils
from .utils import send_notification

# Models
from .models import (
    User,
    Event,
    EventParticipation,
    ActivityLog,
    Checkin,
    Reward,
    RewardRedeem,
    Notification,
    Profile,
    Post,
    LikePost,
    Followers,
    Comment,
    Message,
    ParticipationCertificate,    # 👈 BẮT BUỘC CÓ
)


# ===================================
# 🏠 HOME
# ===================================
def home(request):
    events = Event.objects.filter(status='upcoming')[:3]
    top_users = User.objects.order_by('-points')[:5]

    for u in top_users:
        u.event_count = EventParticipation.objects.filter(user=u).count()

    # 🔥 Lấy danh sách sự kiện user đã đăng ký
    participated_event_ids = []
    if request.user.is_authenticated:
        participated_event_ids = list(
            EventParticipation.objects.filter(user=request.user)
            .values_list("event_id", flat=True)
        )

    return render(request, 'app/home.html', {
        'events': events,
        'top_users': top_users,
        'participated_event_ids': participated_event_ids,   # 👈 truyền vào template
    })


# ===================================
# 🎉 EVENTS
# ===================================
def event_list(request):
    now = timezone.now()

    Event.objects.filter(
        datetime_end__lt=now, status__in=['upcoming', 'in_progress']
    ).update(status='done')

    Event.objects.filter(
        datetime_start__lte=now,
        datetime_end__gte=now,
        status='upcoming'
    ).update(status='in_progress')

    events = Event.objects.all().order_by('-datetime_start')

    participated_event_ids = []
    if request.user.is_authenticated:
        participated_event_ids = EventParticipation.objects.filter(
            user=request.user
        ).values_list("event_id", flat=True)

    return render(request, 'app/event_list.html', {
        'events': events,
        'participated_event_ids': participated_event_ids,
    })



@login_required
def my_events(request):
    participations = EventParticipation.objects.filter(
        user=request.user
    ).select_related('event')

    registered_events = [p.event for p in participations if p.event.status in ['upcoming', 'in_progress']]
    completed_events = [p.event for p in participations if p.event.status == 'done']

    return render(request, 'app/my_events.html', {
        'registered_events': registered_events,
        'completed_events': completed_events
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    now = timezone.now()

    # Update status
    if event.datetime_end < now and event.status != 'done':
        event.status = 'done'
        event.save()

        if request.user.is_authenticated and EventParticipation.objects.filter(user=request.user, event=event).exists():
            send_notification(
                request.user,
                "🏁 Hoàn thành sự kiện",
                f"Bạn đã hoàn thành '{event.title}'. Cảm ơn bạn 🌱",
                "event"
            )

    elif event.datetime_start <= now < event.datetime_end and event.status != 'in_progress':
        event.status = 'in_progress'
        event.save()

    elif now < event.datetime_start and event.status != 'upcoming':
        event.status = 'upcoming'
        event.save()

    is_registered = request.user.is_authenticated and EventParticipation.objects.filter(
        user=request.user, event=event
    ).exists()

    has_checked_in = request.user.is_authenticated and Checkin.objects.filter(
        user=request.user, event=event
    ).exists()

    return render(request, 'app/event_detail.html', {
        'event': event,
        'is_registered': is_registered,
        'has_checked_in': has_checked_in
    })


@login_required
def toggle_event_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if request.method == 'POST':
        participation = EventParticipation.objects.filter(user=user, event=event).first()

        if participation:
            participation.delete()
            event.participants_current = max(0, event.participants_current - 1)
            msg = "❌ Bạn đã hủy đăng ký sự kiện."
            action = 'delete'
        else:
            EventParticipation.objects.create(user=user, event=event)
            event.participants_current += 1
            msg = "🎉 Đăng ký thành công!"
            action = 'create'

        messages.info(request, msg)
        event.save()

        ActivityLog.objects.create(
            user=user,
            action_type=action,
            description=f"{user.username} {msg}",
            related_table='EventParticipation',
            related_id=event.id
        )

    return redirect('event_detail', event.id)


@login_required
def generate_event_otp(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "🚫 Không có quyền.")
        return redirect('home')

    event = get_object_or_404(Event, id=event_id)
    event.generate_otp()

    messages.success(request, f"OTP {event.otp_code} đã tạo.")
    return redirect('event_detail', event.id)


@login_required
def checkin_via_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        now = timezone.now()
        user = request.user

        event = Event.objects.filter(otp_code=otp).first()

        if not event:
            messages.error(request, "❌ OTP không hợp lệ.")
            return redirect("checkin_via_otp")

        if not (event.datetime_start <= now <= event.datetime_end):
            messages.error(request, "⚠️ OTP hết hạn hoặc chưa tới giờ.")
            return redirect("checkin_via_otp")

        if Checkin.objects.filter(user=user, event=event).exists():
            messages.info(request, "Bạn đã điểm danh rồi.")
            return redirect("event_detail", event.id)

        # 1️⃣ Tạo checkin
        Checkin.objects.create(
            user=user,
            event=event,
            verified=True,
            verified_by=user
        )

        # 2️⃣ Cộng điểm
        user.points += event.points
        user.save()

        # 3️⃣ Gửi thông báo
        send_notification(
            user,
            "🎯 Điểm danh thành công",
            f"Bạn đã điểm danh '{event.title}' lúc {now:%H:%M %d/%m/%Y}",
            "event"
        )

        # 4️⃣ Tạo file PDF
        filepath = generate_certificate(user, event)
        filename = os.path.basename(filepath)

        # 5️⃣ Lưu vào FileField
        from django.core.files import File
        with open(filepath, "rb") as f:
            ParticipationCertificate.objects.create(
                user=user,
                event=event,
                file=File(f, name=filename),
                approved=False
            )

        messages.success(request, "🎉 Điểm danh thành công! Giấy chứng nhận đã được tạo.")
        return redirect("event_detail", event.id)

    return render(request, "app/checkin.html")






# ===================================
# 👤 AUTH (LOGIN / REGISTER / LOGOUT)
# ===================================
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']
        confirm = request.POST['confirm_password']

        if password != confirm:
            messages.error(request, "Mật khẩu không khớp.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập tồn tại.")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password
        )

        avatar = request.FILES.get('avatar')
        if avatar:
            user.avatar = avatar
            user.save()

        messages.success(request, "Đăng ký thành công.")
        return redirect('login')

    return render(request, 'app/register.html')


def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, "Sai tài khoản hoặc mật khẩu.")

    return render(request, 'app/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Đã đăng xuất.")
    return redirect('home')


# ===================================
# 👤 PROFILE
# ===================================
@login_required
def profile_view(request):
    return render(request, 'app/profile.html', {'user': request.user})


@login_required
def profile_edit_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cập nhật thành công.")
        return redirect('profile')

    return render(request, 'app/profile_edit.html', {'form': form})


# ===================================
# 🎁 REWARDS
# ===================================
@login_required
def redeem_rewards(request):
    rewards = Reward.objects.all().order_by('-created_at')

    if request.method == 'POST':
        reward = get_object_or_404(Reward, id=request.POST['reward_id'])
        quantity = int(request.POST.get('quantity', 1))
        total = reward.required_points * quantity

        if request.user.points < total:
            messages.error(request, "Không đủ điểm.")
            return redirect('redeem_rewards')

        if reward.stock < quantity:
            messages.error(request, "Không đủ số lượng.")
            return redirect('redeem_rewards')

        request.user.points -= total
        reward.stock -= quantity
        reward.save()
        request.user.save()

        RewardRedeem.objects.create(
            user=request.user,
            reward=reward,
            quantity=quantity,
            points_spent=total,
            status='approved'
        )

        messages.success(request, "Đổi quà thành công.")
        return redirect('redeem_rewards')

    return render(request, 'app/redeem_rewards.html', {'rewards': rewards})


@login_required
def my_reward_history(request):
    history = RewardRedeem.objects.filter(
        user=request.user
    ).select_related('reward').order_by('-redeem_date')

    return render(request, 'app/reward_history.html', {'history': history})


# ===================================
# 🔔 NOTIFICATIONS
# ===================================
@login_required
def notifications_view(request):
    noti = Notification.objects.filter(user=request.user).order_by('-sent_at')
    noti.update(is_read=True)
    return render(request, 'app/notifications.html', {'notifications': noti})


# ===================================
# 🌿 SOCIAL NETWORK (POSTS, COMMENTS)
# ===================================
@login_required
def social_home(request):
    posts = Post.objects.all().order_by('-created_at')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'app/social_home.html', {'posts': posts, 'profile': profile})


@login_required
def upload_post(request):
    if request.method == 'POST':
        Post.objects.create(
            user=request.user,
            image=request.FILES.get('image_upload'),
            caption=request.POST.get('caption', '')
        )
    return redirect('social_home')


@login_required
def like_post(request, id):
    post = get_object_or_404(Post, id=id)
    like = LikePost.objects.filter(post=post, user=request.user).first()

    if like:
        like.delete()
        post.no_of_likes -= 1
    else:
        LikePost.objects.create(post=post, user=request.user)
        post.no_of_likes += 1

    post.save()
    return redirect('social_home')


@login_required
def follow_user(request):
    if request.method == 'POST':
        target = get_object_or_404(User, username=request.POST['user'])
        item = Followers.objects.filter(follower=request.user, user=target)

        if item.exists():
            item.delete()
        else:
            Followers.objects.create(follower=request.user, user=target)

        return redirect(f'/profile/{target.username}')

    return redirect('social_home')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')

        if not content and not image:
            messages.error(request, "Không được để trống.")
        else:
            Comment.objects.create(
                post=post, user=request.user,
                content=content, image=image
            )

    return redirect('social_home')


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)

    if request.method == 'POST':
        content = request.POST.get("content", "").strip()
        if content:
            comment.content = content
            comment.save()
        else:
            messages.error(request, "Không được để trống.")

        return redirect('social_home')

    return render(request, 'app/edit_comment.html', {'comment': comment})


@login_required
def delete_comment(request, comment_id):
    get_object_or_404(Comment, id=comment_id, user=request.user).delete()
    return redirect('social_home')


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        caption = request.POST.get("caption", "").strip()
        image = request.FILES.get("image_upload")

        if not caption:
            messages.error(request, "Không để trống.")
            return redirect('edit_post', post_id=post.id)

        post.caption = caption
        if image:
            post.image = image
        post.save()

        return redirect('social_home')

    return render(request, 'app/edit_post.html', {'post': post})


@login_required
def delete_post(request, post_id):
    get_object_or_404(Post, id=post_id, user=request.user).delete()
    return redirect('social_home')


# ===================================
# 🤖 CHATBOT – FULL CODE
# ===================================

import re
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import (
    Message,
    Profile,
    EventParticipation,
    RewardRedeem,
    Report,
    User,
)

# =========================
# INTENTS
# =========================
CHATBOT_INTENTS = {
    "points": ["điểm", "bao nhiêu điểm", "point"],
    "health": ["sức khỏe", "health", "điểm xanh"],
    "events": ["sự kiện", "event", "tham gia"],
    "reports": ["báo cáo", "điểm rác", "rác"],
    "rewards": ["quà", "đổi quà", "phần thưởng"],
    "ranking": ["xếp hạng", "top", "rank"],
    "help": ["giúp", "hướng dẫn", "làm sao", "help"],
}

# =========================
# HELPERS
# =========================
def chatbot_normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text


def chatbot_detect_intent(text: str):
    for intent, keys in CHATBOT_INTENTS.items():
        for k in keys:
            if k in text:
                return intent
    return None


def chatbot_handle_intent(user, intent):
    profile, _ = Profile.objects.get_or_create(user=user)

    if intent == "points":
        return f"🌿 Bạn đang có <b>{user.points}</b> điểm xanh."

    if intent == "health":
        return f"💚 Điểm sức khỏe môi trường: <b>{profile.health_score}/100</b>."

    if intent == "events":
        count = EventParticipation.objects.filter(user=user).count()
        return f"📅 Bạn đã tham gia <b>{count}</b> sự kiện."

    if intent == "reports":
        total = Report.objects.filter(user=user).count()
        approved = Report.objects.filter(
            user=user, admin_status="approved"
        ).count()
        return (
            f"🗑 Bạn đã gửi <b>{total}</b> báo cáo.<br>"
            f"✔ <b>{approved}</b> báo cáo đã được xác minh."
        )

    if intent == "rewards":
        used = RewardRedeem.objects.filter(user=user).count()
        return f"🎁 Bạn đã đổi <b>{used}</b> phần thưởng."

    if intent == "ranking":
        ranking = list(
            User.objects.order_by("-points").values_list("id", flat=True)
        )
        rank = ranking.index(user.id) + 1 if user.id in ranking else "N/A"
        return f"🏆 Thứ hạng của bạn: <b>#{rank}</b>."

    if intent == "help":
        return (
            "🤖 Tôi có thể giúp bạn:<br>"
            "• Kiểm tra điểm 🌿<br>"
            "• Sức khỏe môi trường 💚<br>"
            "• Sự kiện 📅<br>"
            "• Báo cáo rác 🗑<br>"
            "• Đổi quà 🎁<br>"
            "• Xếp hạng 🏆"
        )

    return "🤖 Tôi chưa hiểu. Hãy chọn câu hỏi bên dưới 👇"


# =========================
# CHAT PAGE (HTML)
# =========================
@login_required
def chat_page(request):
    messages = Message.objects.filter(sender=request.user).order_by("sent_at")

    suggestions = [
        "Tôi có bao nhiêu điểm?",
        "Sức khỏe môi trường của tôi thế nào?",
        "Tôi đã tham gia mấy sự kiện?",
        "Tôi đã báo cáo mấy điểm rác?",
        "Xếp hạng của tôi hiện tại?",
        "Làm sao để đổi quà?",
    ]

    return render(
        request,
        "app/chat_page.html",
        {
            "messages": messages,
            "suggestions": suggestions,
        }
    )


# =========================
# CHAT API (AJAX)
# =========================
@login_required
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user
    text = request.POST.get("message", "").strip()

    Message.objects.create(
        sender=user,
        content=text,
        is_from_bot=False
    )

    intent = chatbot_detect_intent(chatbot_normalize(text))
    reply = chatbot_handle_intent(user, intent)

    Message.objects.create(
        sender=user,
        content=reply,
        is_from_bot=True
    )

    # Gợi ý theo ngữ cảnh (demo)
    followups = {
        "points": ["Xếp hạng của tôi?", "Làm sao để đổi quà?"],
        "health": ["Tôi đã tham gia mấy sự kiện?"],
        "events": ["Sự kiện sắp tới?", "Xem điểm của tôi"],
    }

    return JsonResponse({
        "response": reply,
        "suggestions": followups.get(intent, [
            "Tôi có bao nhiêu điểm?",
            "Sức khỏe môi trường của tôi thế nào?",
        ])
    })



# ===================================
# 📄 QUẢN LÝ GIẤY CHỨNG NHẬN (ADMIN)
# ===================================
@staff_member_required
def certificate_list(request):
    waiting = ParticipationCertificate.objects.filter(approved=False)
    approved = ParticipationCertificate.objects.filter(approved=True)

    return render(request, "app/certificate_list.html", {
        "waiting": waiting,
        "approved": approved,
    })
@staff_member_required
def approve_certificate(request, cert_id):
    cert = get_object_or_404(ParticipationCertificate, id=cert_id)
    cert.approved = True
    cert.approved_at = timezone.now()
    cert.approved_by = request.user
    cert.save()

    if cert.user.email:
        email = EmailMessage(
            subject="🎉 Giấy chứng nhận đã được duyệt!",
            body=(
                f"Xin chào {cert.user.username},\n\n"
                f"Giấy chứng nhận tham gia sự kiện '{cert.event.title}' đã được duyệt.\n"
                "Vui lòng xem file PDF đính kèm.\n\n"
                "Trân trọng!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cert.user.email]
        )
        email.attach_file(cert.file.path)
        email.send()

    messages.success(request, "✔ Giấy chứng nhận đã được duyệt & gửi email.")
    return redirect("certificate_list")



def generate_certificate(user, event):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    # Font Unicode
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

    # Thư mục lưu file PDF
    folder = "media/certificates/"
    os.makedirs(folder, exist_ok=True)

    filename = f"certificate_{user.id}_{event.id}.pdf"
    filepath = os.path.join(folder, filename)

    # PDF
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # ===== LOGO =====
    logo = "app/static/app/images/logo.jpg"
    if os.path.exists(logo):
        c.drawImage(
            logo,
            width/2 - 1.8*cm,
            height - 5*cm,
            width=3.6*cm,
            preserveAspectRatio=True,
            mask="auto",
        )

    # ===== TIÊU ĐỀ =====
    c.setFont("Arial-Bold", 38)
    c.setFillColorRGB(0, 0.45, 0)
    c.drawCentredString(width/2, height - 7*cm, "Thư cảm ơn")

    # ===== SUBTITLE =====
    c.setFont("Arial-Bold", 20)
    c.drawCentredString(width/2, height - 8.5*cm, "GOGREEN CLEANUP")

    c.setFont("Arial", 12)
    c.drawCentredString(width/2, height - 9.6*cm, "xin chân thành cảm ơn")

    # ===== TÊN NGƯỜI NHẬN =====
    c.setFont("Arial-Bold", 22)
    c.drawCentredString(width/2, height - 11*cm, user.username)

    # Gạch chân
    c.setLineWidth(1)
    c.line(width/2 - 4*cm, height - 11.3*cm, width/2 + 4*cm, height - 11.3*cm)

    # ===== NỘI DUNG =====
    c.setFont("Arial", 12)
    lines = [
        "đã tham gia tích cực hỗ trợ trong công tác dọn dẹp, tuyên truyền",
        "và bảo vệ môi trường tại địa bàn TP. HCM.",
        "",
        "GoGreen Cleanup xin kính chúc Quý Anh/Chị thật nhiều sức khỏe",
        "và thành công trong cuộc sống."
    ]

    y = height - 14*cm
    for line in lines:
        c.drawCentredString(width/2, y, line)
        y -= 0.8*cm

    # ===== NGÀY =====
    today = timezone.now()
    date_text = f"TP. HCM, ngày {today.day} tháng {today.month} năm {today.year}"
    c.drawString(width - 13*cm, 6.2*cm, date_text)

    # ===== CHỮ KÝ =====
    sign_path = "app/static/app/images/signature.jpg"
    if os.path.exists(sign_path):
        c.drawImage(
            sign_path,
            width - 11*cm,
            3.8*cm,
            width=4*cm,
            preserveAspectRatio=True,
            mask="auto",
        )

    # ===== TEXT DƯỚI CHỮ KÝ =====
    c.setFont("Arial-Bold", 12)
    c.setFillColorRGB(0, 0.45, 0)
    c.drawString(width - 10*cm, 2.8*cm, "GO GREEN CLEANUP")

    c.save()
    return filepath
# ===================================
# ⚡ ĐĂNG KÝ NHANH SỰ KIỆN
# ===================================
@login_required
def quick_register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if request.method == "POST":
        participation = EventParticipation.objects.filter(user=user, event=event).first()

        if participation:
            # ✅ Nếu đã đăng ký → Hủy
            participation.delete()
            event.participants_current = max(0, event.participants_current - 1)
            event.save()

            ActivityLog.objects.create(
                user=user,
                action_type='delete',
                description=f"{user.username} đã hủy đăng ký nhanh sự kiện '{event.title}'",
                related_table='EventParticipation',
                related_id=event.id
            )

            messages.warning(request, f"❌ Bạn đã hủy đăng ký sự kiện '{event.title}'.")
        else:
            # ✅ Nếu chưa đăng ký → Đăng ký mới
            if event.participants_current >= event.participants_max:
                messages.warning(request, "⚠️ Sự kiện đã đủ người tham gia.")
            else:
                EventParticipation.objects.create(user=user, event=event)
                event.participants_current += 1
                event.save()

                ActivityLog.objects.create(
                    user=user,
                    action_type='create',
                    description=f"{user.username} đã đăng ký nhanh sự kiện '{event.title}'",
                    related_table='EventParticipation',
                    related_id=event.id
                )

                messages.success(request, f"✅ Đăng ký nhanh sự kiện '{event.title}' thành công!")

    # Quay lại trang hiện tại
    return redirect(request.META.get("HTTP_REFERER", "home"))



@staff_member_required
def admin_dashboard(request):
    stats = {
        "total_users": User.objects.count(),  # Tổng người dùng / tình nguyện viên
        "total_events": Event.objects.count(),  # Số sự kiện
        "total_participations": EventParticipation.objects.count(),  # Người tham gia
        "total_rewards": Reward.objects.count(),  # Số quà
        "total_redeems": RewardRedeem.objects.count(),  # Số lượt đổi thưởng
        "total_posts": Post.objects.count(),  # Số bài đăng
        "total_trash_reports": Message.objects.count(),  # hoặc Report nếu bạn có
    }

    return render(request, "admin/custom_dashboard.html", {"stats": stats})


import json
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

GOOGLE_CLIENT_ID = "489908808640-9i76sqlsldk4nott5dugbn4oa9orf5jg.apps.googleusercontent.com"


@csrf_exempt
def google_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("credential")

        try:
            # Verify token from Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )

            email = idinfo["email"]
            name = idinfo.get("name", email.split("@")[0])
            picture = idinfo.get("picture", "")

            # Create or get user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                }
            )

            # Update name or avatar if muốn:
            if created:
                user.first_name = name
                if hasattr(user, "avatar") and picture:
                    user.avatar = picture
                user.save()

            login(request, user)
            return JsonResponse({"status": "ok"})

        except Exception as e:
            print("Google Login Error:", e)
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "invalid"})



from .models import Report
from django.core.mail import send_mail


   
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.mail import EmailMessage

from .models import Report


def _to_float(value):
    """Ép kiểu float an toàn; trả None nếu không hợp lệ."""
    try:
        if value in (None, "", "null", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_admin_user(user):
    """Hỗ trợ cả role-based và staff-based."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    return getattr(user, "role", "") == "admin"


# ===================================
# 📌 REPORT: USER TẠO BÁO CÁO
# ===================================

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .ai import analyze_images

from .models import Report
from app.ai import analyze_images




def _to_float(value):
    """Ép kiểu float an toàn; trả None nếu rỗng/không hợp lệ."""
    try:
        if value in (None, "", "null", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_admin_user(user):
    """Admin theo Django staff/superuser hoặc theo role='admin' (nếu bạn có field role)."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    return getattr(user, "role", "") == "admin"


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Report
from .ai import analyze_images



def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =========================
# 🗑 USER: TẠO BÁO CÁO
# =========================
@login_required
def create_report(request):
    if request.method == "POST":
        img = request.FILES.get("images")
        lat = parse_float(request.POST.get("lat"))
        lng = parse_float(request.POST.get("lng"))
        desc = (request.POST.get("description") or "").strip()

        if not img:
            messages.error(request, "Vui lòng tải lên hình ảnh điểm rác.")
            return redirect("report_create")

        report = Report.objects.create(
            user=request.user,
            images=img,
            lat=lat,
            lng=lng,
            description=desc,
        )

        # AI phân tích
        try:
            ai = analyze_images([report.images.path])
        except Exception:
            report.analysis_summary = (
                "AI chưa thể phân tích tại thời điểm này. "
                "Báo cáo đã được chuyển admin xác minh."
            )
            report.save(update_fields=["analysis_summary"])
            messages.warning(
                request,
                "Báo cáo đã gửi, AI chưa phân tích được."
            )
            return redirect("report_detail", report.id)

        trash_types = ai.get("trash_types", [])
        report.predicted_trash_type = trash_types[0] if trash_types else None
        report.estimated_weight_ton = ai.get("weight", 0)
        report.recommended_volunteers = ai.get("volunteers", 0)
        report.analysis_summary = ai.get("summary", "")
        report.save()

        # Email cảm ơn
        if request.user.email:
            EmailMessage(
                subject="Cam on ban da bao cao diem rac",
                body=(
                    f"Xin chao {request.user.username},\n\n"
                    "Bao cao diem rac cua ban da duoc tiep nhan.\n"
                    "Cam on ban da chung tay bao ve moi truong."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email],
            ).send(fail_silently=True)

        messages.success(request, "Báo cáo đã gửi thành công.")
        return redirect("report_detail", report.id)

    return render(request, "app/report_create.html")


# =========================
# 📄 CHI TIẾT REPORT
# =========================
@login_required
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.user != report.user and not request.user.is_staff:
        messages.error(request, "Bạn không có quyền xem báo cáo này.")
        return redirect("home")

    return render(request, "app/report_detail.html", {"report": report})


# =========================
# 🛠 ADMIN: DANH SÁCH
# =========================
@staff_member_required
def admin_report_list(request):
    reports = Report.objects.all().order_by("-created_at")
    return render(request, "admin/report_list.html", {"reports": reports})


# =========================
# ✅ ADMIN: DUYỆT REPORT
# =========================
@staff_member_required
def admin_verify_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if report.admin_status != Report.Status.APPROVED:
        report.admin_status = Report.Status.APPROVED
        report.verified_at = timezone.now()
        report.save(update_fields=["admin_status", "verified_at"])

        if report.user.email:
            EmailMessage(
                subject="Bao cao diem rac da duoc xac minh",
                body=(
                    f"Xin chao {report.user.username},\n\n"
                    "Bao cao diem rac cua ban da duoc admin xac minh.\n\n"
                    f"Loai rac: {report.get_predicted_trash_type_display()}\n"
                    f"Khoi luong: {report.estimated_weight_ton} tan\n"
                    f"So nguoi goi y: {report.recommended_volunteers}\n\n"
                    "Cam on ban."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[report.user.email],
            ).send(fail_silently=True)

        messages.success(request, "Báo cáo đã được duyệt.")

    return redirect("admin_report_list")

from django.shortcuts import render, redirect
from .utils import send_otp

def login_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        send_otp(email)
        request.session["otp_email"] = email
        return redirect("verify_otp")
    return render(request, "login_email.html")

from django.contrib.auth import get_user_model, login
from django.utils import timezone
from .models import EmailOTP

User = get_user_model()

def verify_otp(request):
    email = request.session.get("otp_email")

    if not email:
        return redirect("login_email")

    if request.method == "POST":
        otp = request.POST.get("otp")

        record = EmailOTP.objects.filter(
            email=email,
            otp=otp,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()

        if record:
            record.is_used = True
            record.save()

            user, _ = User.objects.get_or_create(
                email=email,
                defaults={"username": email.split("@")[0]}
            )

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend"
            )

            return redirect("/")

    return render(request, "verify_otp.html")
