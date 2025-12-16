from django.contrib import admin
from app.models import ActivityLog, UserBadge, TrashCategory
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "description", "created_at")
@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge_name", "achieved_at")
@admin.register(TrashCategory)
class TrashCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
