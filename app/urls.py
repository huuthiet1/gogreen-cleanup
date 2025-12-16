from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("app.urls.home")),
    path("", include("app.urls.events")),
    path("", include("app.urls.auth")),
    path("", include("app.urls.profile")),
    path("", include("app.urls.rewards")),
    path("", include("app.urls.notifications")),
    path("", include("app.urls.social")),
    path("", include("app.urls.chatbot")),
    path("", include("app.urls.reports")),
    path("", include("app.urls.otp")),

    path("admin/", include("app.urls.admin")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]
