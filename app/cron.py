from django.utils import timezone
from django.core.mail import send_mail
from app.models import Event, EventParticipation, Notification

def send_event_reminders():
    now = timezone.now()
    next_day = now + timezone.timedelta(days=1)
    events = Event.objects.filter(datetime_start__date=next_day.date(), status='upcoming')

    for event in events:
        for p in EventParticipation.objects.filter(event=event).select_related('user'):
            user = p.user
            if not user.email:
                continue

            subject = f"🌿 Nhắc lịch sự kiện: {event.title}"
            message = (
                f"Chào {user.username},\n\n"
                f"Sự kiện '{event.title}' sẽ diễn ra vào "
                f"{event.datetime_start.strftime('%H:%M, %d/%m/%Y')} tại {event.address or 'địa điểm chỉ định'}.\n\n"
                "Hãy chuẩn bị găng tay, nước uống và tinh thần xanh nhé 💚\n\n"
                "-- Go Green Clean Up 🌍"
            )

            send_mail(subject, message, None, [user.email])

            # ✅ Ghi thông báo hệ thống
            Notification.objects.create(
                user=user,
                title="⏰ Nhắc lịch sự kiện ngày mai",
                message=f"Sự kiện '{event.title}' sẽ diễn ra vào {event.datetime_start.strftime('%H:%M, %d/%m/%Y')}.",
                type="reminder"
            )
