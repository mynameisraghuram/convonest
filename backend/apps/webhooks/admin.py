# backend/apps/webhooks/admin.py

from django.contrib import admin

from .models import WhatsappWebhookConfig, WebhookEventLog


@admin.register(WhatsappWebhookConfig)
class WhatsappWebhookConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "verify_token", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "verify_token")


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "config",
        "processing_status",
        "created_at",
        "processed_at",
        "delivery_attempts",
    )
    list_filter = ("processing_status", "created_at")
    search_fields = ("id", "error_message")
