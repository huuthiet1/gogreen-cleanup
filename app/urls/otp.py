from django.urls import path
from app.views.auth import login_email, verify_otp

urlpatterns = [
    path("login-email/", login_email, name="login_email"),
    path("verify-otp/", verify_otp, name="verify_otp"),
]
