from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import Message, Profile, EventParticipation


@login_required
def chat_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        text = request.POST.get("message", "").lower()

        Message.objects.create(sender=user, content=text)

        if "điểm" in text:
            reply = f"🌿 Bạn có {user.points} điểm."
        elif "sự kiện" in text:
            reply = f"📅 Bạn đã tham gia {EventParticipation.objects.filter(user=user).count()} sự kiện."
        else:
            reply = "🤖 Mình chưa hiểu."

        Message.objects.create(sender=user, content=reply, is_from_bot=True)
        return JsonResponse({"response": reply})
