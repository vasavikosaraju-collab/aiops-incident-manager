from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("AIOps", {"fields": ("role", "team")}),
    )
    list_display = ("username", "email", "role", "team", "is_staff")
    list_filter = ("role", "team", "is_staff", "is_active")
