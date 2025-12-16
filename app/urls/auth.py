from django.urls import path
from app.views.auth import (
    login_view, register_view, logout_view,
    google_login
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("google-login/", google_login, name="google_login"),
]
