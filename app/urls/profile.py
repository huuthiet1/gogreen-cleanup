from django.urls import path
from app.views.auth import profile_view, profile_edit_view

urlpatterns = [
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
]
