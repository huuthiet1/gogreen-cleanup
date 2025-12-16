from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from ..models import Report
from ..ai import analyze_images


@login_required
def create_report(request):
    if request.method == "POST":
        img = request.FILES.get("images")
        if not img:
            messages.error(request, "Cần hình ảnh.")
            return redirect("report_create")

        report = Report.objects.create(
            user=request.user,
            images=img,
            description=request.POST.get("description", "")
        )

        try:
            ai = analyze_images([report.images.path])
            report.analysis_summary = ai.get("summary", "")
            report.save()
        except Exception:
            pass

        messages.success(request, "Đã gửi báo cáo.")
        return redirect("report_detail", report.id)

    return render(request, "app/report_create.html")
