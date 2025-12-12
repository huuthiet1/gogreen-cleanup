from django.contrib.admin import AdminSite
from django.db.models import Count, Sum
from app.models import User, Event, EventParticipation, Report, RewardRedeem

class CustomAdmin(AdminSite):

    def each_context(self, request):
        context = super().each_context(request)

        context.update({
            "stats": {
                "users": User.objects.count(),
                "events": Event.objects.count(),
                "participations": EventParticipation.objects.count(),
                "trash_reports": Report.objects.count(),
                "redeems": RewardRedeem.objects.count(),
            }
        })
        return context

custom_admin_site = CustomAdmin()
