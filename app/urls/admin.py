from django.urls import path
from app.views.admin import admin_dashboard, quick_register_event

urlpatterns = [
    path("", admin_dashboard, name="admin_dashboard"),
    path("quick-register/<int:event_id>/", quick_register_event, name="quick_register"),
]
