from django.contrib import admin
from django.urls import path, include
from . import views
from app.views import admin_dashboard, quick_register_event
from .views import login_email, verify_otp


urlpatterns = [

    # ===== Trang chính =====
    path('', views.home, name="home"),

    # ===== Trang sự kiện =====
    path('events/', views.event_list, name="cart"),
    path('my-events/', views.my_events, name="checkout"),

    # ===== Chi tiết sự kiện =====
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/toggle/', views.toggle_event_registration, name='toggle_event_registration'),
    path('event/<int:event_id>/quick-toggle/', quick_register_event, name='quick_register'),

    # ===== Auth =====
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ===== Hồ sơ =====
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # ===== OTP =====
    path('event/<int:event_id>/generate-otp/', views.generate_event_otp, name='generate_event_otp'),
    path('checkin/', views.checkin_via_otp, name='checkin_via_otp'),

    # ===== Rewards =====
    path('rewards/', views.redeem_rewards, name='redeem_rewards'),
    path('rewards/history/', views.my_reward_history, name='reward_history'),

    # ===== Notifications =====
    path('notifications/', views.notifications_view, name='notifications'),

    # ===== Social =====
    path('social/', views.social_home, name='social_home'),
    path('social/upload/', views.upload_post, name='upload_post'),
    path('social/like/<uuid:id>/', views.like_post, name='like_post'),
    path('social/comment/<uuid:post_id>/', views.add_comment, name='add_comment'),
    path('social/comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('social/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('social/post/edit/<uuid:post_id>/', views.edit_post, name='edit_post'),
    path('social/post/delete/<uuid:post_id>/', views.delete_post, name='delete_post'),

    # ===== Chatbot =====
    path("chat/", views.chat_view, name="chatbot"),

    # ===== Certificates =====
    path("admin/certificates/", views.certificate_list, name="certificate_list"),
    path("admin/certificates/approve/<int:cert_id>/", views.approve_certificate, name="approve_certificate"),

    # ===== Google Login =====
    path("google-login/", views.google_login, name="google_login"),

    # ===== REPORT =====
    path("report/create/", views.create_report, name="create_report"),
    path("report/<int:report_id>/", views.report_detail, name="report_detail"),

    path("admin/reports/", views.admin_report_list, name="admin_report_list"),
    path("admin/report/verify/<int:report_id>/", views.admin_verify_report, name="admin_verify_report"),


    # ===== Django Admin =====
    path("admin/", admin.site.urls),
    path("accounts/", include('allauth.urls')),

    path("login-email/", login_email, name="login_email"),
    path("verify-otp/", verify_otp, name="verify_otp"),
]
