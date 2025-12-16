from django.urls import path
from app.views.reports import (
    create_report, report_detail,
    admin_report_list, admin_verify_report
)

urlpatterns = [
    path("report/create/", create_report, name="create_report"),
    path("report/<int:report_id>/", report_detail, name="report_detail"),

    path("admin/reports/", admin_report_list, name="admin_report_list"),
    path("admin/report/verify/<int:report_id>/", admin_verify_report, name="admin_verify_report"),
]
