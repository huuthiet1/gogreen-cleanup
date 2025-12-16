from django.urls import path
from app.views.notifications import notifications_view

urlpatterns = [
    path("notifications/", notifications_view, name="notifications"),
]
