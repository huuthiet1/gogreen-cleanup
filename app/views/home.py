from django.shortcuts import render
from django.db.models import Count
from ..models import Event, User, EventParticipation

def home(request):
    events = Event.objects.filter(status='upcoming').order_by('datetime_start')[:3]

    top_users = (
        User.objects
        .annotate(event_count=Count('eventparticipation'))
        .order_by('-points')[:5]
    )

    participated_event_ids = []
    if request.user.is_authenticated:
        participated_event_ids = list(
            EventParticipation.objects
            .filter(user=request.user)
            .values_list('event_id', flat=True)
        )

    return render(request, 'app/home.html', {
        'events': events,
        'top_users': top_users,
        'participated_event_ids': participated_event_ids
    })
