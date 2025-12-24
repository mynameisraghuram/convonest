# D:\convonest\backend\apps\whatsapp_accounts\admin.py

from django.contrib import admin
from .models import (
    WhatsappBusinessAccount,
    WhatsappPhoneNumber,
    WhatsappContact,
    WhatsappConversation,
    WhatsappQrCode,
)


@admin.register(WhatsappBusinessAccount)
class WhatsappBusinessAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "meta_business_id", "status")
    search_fields = ("id", "name", "meta_business_id")


@admin.register(WhatsappPhoneNumber)
class WhatsappPhoneNumberAdmin(admin.ModelAdmin):
    list_display = (
        "e164_number",
        "display_name",
        "waba",
        "registered",
        "two_step_enabled",
        "test_number",
        "display_name_status",
        "oba_status",
    )
    list_filter = (
        "registered",
        "two_step_enabled",
        "test_number",
        "display_name_status",
        "oba_status",
    )
    search_fields = ("e164_number", "display_name", "id")


@admin.register(WhatsappContact)
class WhatsappContactAdmin(admin.ModelAdmin):
    list_display = ("bsuid", "phone", "wa_username", "created_at")
    search_fields = ("bsuid", "phone", "wa_username")


@admin.register(WhatsappConversation)
class WhatsappConversationAdmin(admin.ModelAdmin):
    list_display = ("contact", "phone_number", "category", "opened_at", "expires_at")
    list_filter = ("category",)
    search_fields = ("contact__bsuid", "phone_number__e164_number")


@admin.register(WhatsappQrCode)
class WhatsappQrCodeAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "waba", "phone_number", "created_at")
    search_fields = ("name", "id", "phone_number__e164_number")
