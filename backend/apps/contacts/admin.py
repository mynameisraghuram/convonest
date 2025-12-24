# backend/apps/contacts/admin.py

from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "email",
        "language",
        "is_opted_out",
        "is_blocked",
        "last_seen_at",
        "created_at",
    )
    list_filter = ("language", "is_opted_out", "is_blocked")
    search_fields = ("full_name", "phone", "email", "tags")
    ordering = ("full_name", "phone")
    readonly_fields = ("created_at", "updated_at", "last_seen_at")

    fieldsets = (
        ("Basic", {"fields": ("full_name", "phone", "email")}),
        ("Preferences", {"fields": ("language", "timezone")}),
        ("Flags", {"fields": ("is_opted_out", "is_blocked")}),
        ("Segmentation", {"fields": ("tags", "extra")}),
        ("System", {"fields": ("last_seen_at", "created_at", "updated_at")}),
    )
