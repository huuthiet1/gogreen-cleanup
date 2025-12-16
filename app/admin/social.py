from django.contrib import admin
from django.utils.html import format_html
from app.models import (
    Profile, Post, LikePost, Followers,
    EventComment, Message
)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "health_score", "location")
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("preview", "user", "caption", "created_at", "no_of_likes")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80"/>', obj.image.url)
        return "—"
@admin.register(LikePost)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ("user", "post")
@admin.register(Followers)
class FollowersAdmin(admin.ModelAdmin):
    list_display = ("follower", "user")
@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "created_at")
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "is_from_bot", "sent_at")
