from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/toggle/', views.toggle_event_registration, name='toggle_event_registration'),

     # ⭐ ALLAUTH – GOOGLE LOGIN BẮT BUỘC
    path('accounts/', include('allauth.urls')),
    path("", include("app.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'app' / 'static')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
