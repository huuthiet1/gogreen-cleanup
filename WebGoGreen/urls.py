from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from django.shortcuts import redirect

# =========================
# ALIAS ADMIN COMMENT
# =========================
def admin_comment_redirect(request):
    return redirect("/admin/app/eventcomment/")

urlpatterns = [

    # ✅ PHẢI ĐẶT TRƯỚC admin/
    path("admin/app/comment/", admin_comment_redirect),

    # ===== DJANGO ADMIN =====
    path('admin/', admin.site.urls),

    # ===== APP URLS =====
    path('', include('app.urls')),

    # ===== AUTH (ALLAUTH) =====
    path('accounts/', include('allauth.urls')),
]

# ===== STATIC & MEDIA (LOCAL) =====
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.BASE_DIR / 'app' / 'static'
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
