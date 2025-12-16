from django.urls import path
from app.views.certificates import certificate_list, approve_certificate

urlpatterns = [
    path("admin/certificates/", certificate_list, name="certificate_list"),
    path("admin/certificates/approve/<int:cert_id>/", approve_certificate, name="approve_certificate"),
]
