from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction
from ..models import Event, EventParticipation, Checkin
from ..utils import send_notification

def event_list(request):
    events = Event.objects.all().order_by('-datetime_start')

    participated_ids = []
    if request.user.is_authenticated:
        participated_ids = EventParticipation.objects.filter(
            user=request.user
        ).values_list('event_id', flat=True)

    return render(request, 'app/event_list.html', {
        'events': events,
        'participated_event_ids': participated_ids
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    now = timezone.now()

    is_registered = False
    has_checked_in = False

    if request.user.is_authenticated:
        is_registered = EventParticipation.objects.filter(
            user=request.user, event=event
        ).exists()

        has_checked_in = Checkin.objects.filter(
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

    with transaction.atomic():
        participation = EventParticipation.objects.filter(
            user=request.user, event=event
        ).select_for_update().first()

        if participation:
            participation.delete()
            event.participants_current = max(0, event.participants_current - 1)
            msg = "❌ Hủy đăng ký sự kiện."
        else:
            if event.participants_current >= event.participants_max:
                messages.warning(request, "Sự kiện đã đủ người.")
                return redirect('event_detail', event.id)

            EventParticipation.objects.create(
                user=request.user, event=event
            )
            event.participants_current += 1
            msg = "🎉 Đăng ký sự kiện thành công."

        event.save()

    messages.info(request, msg)
    return redirect('event_detail', event.id)
@login_required
def checkin_via_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        user = request.user
        now = timezone.now()

        event = Event.objects.filter(otp_code=otp).first()
        if not event or not (event.datetime_start <= now <= event.datetime_end):
            messages.error(request, "OTP không hợp lệ hoặc hết hạn.")
            return redirect("checkin_via_otp")

        if Checkin.objects.filter(user=user, event=event).exists():
            messages.info(request, "Bạn đã check-in.")
            return redirect("event_detail", event.id)

        with transaction.atomic():
            Checkin.objects.create(
                user=user, event=event, verified=True
            )
            user.points += event.points
            user.save()

        send_notification(
            user,
            "🎯 Điểm danh thành công",
            f"Bạn được +{event.points} điểm từ '{event.title}'",
            "event"
        )

        messages.success(request, "Check-in thành công.")
        return redirect("event_detail", event.id)

    return render(request, "app/checkin.html")
