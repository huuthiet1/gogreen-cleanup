from django.contrib import admin
from app.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone", "role", "points", "is_active")
    search_fields = ("username", "email", "phone")
    list_filter = ("role", "is_active")
    readonly_fields = ("date_joined", "last_login")
