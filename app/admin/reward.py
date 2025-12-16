from django.contrib import admin
from django.utils.html import format_html
from app.models import Reward, RewardRedeem


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "required_points", "stock")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60"/>', obj.image.url)
        return "—"


@admin.register(RewardRedeem)
class RewardRedeemAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "points_spent", "status", "redeem_date")
    list_filter = ("status",)
