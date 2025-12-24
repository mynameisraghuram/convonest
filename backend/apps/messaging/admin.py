# backend/apps/messaging/admin.py

from django.contrib import admin
from .models import MessageLog


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    """
    Admin view for WhatsApp messages (inbound + outbound).

    This is mainly for:
    - Debugging message flow
    - Verifying webhook ingestion
    - Checking send / delivery status
    """

    list_display = (
        "id",
        "direction",
        "msg_type",
        "status",
        "contact_phone",
        "contact",
        "waba_phone_number_id",
        "created_at",
    )

    list_filter = (
        "direction",
        "msg_type",
        "status",
        "created_at",
    )

    search_fields = (
        "contact_phone",
        "body_text",
        "waba_message_id",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "direction",
        "msg_type",
        "status",
        "contact",
        "contact_phone",
        "waba_message_id",
        "waba_phone_number_id",
        "context_message_id",
        "body_text",
        "payload",
        "error_code",
        "error_message",
        "sent_at",
        "delivered_at",
        "read_at",
        "received_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "direction",
                    "msg_type",
                    "status",
                    "contact",
                    "contact_phone",
                )
            },
        ),
        (
            "WhatsApp Metadata",
            {
                "fields": (
                    "waba_message_id",
                    "waba_phone_number_id",
                    "context_message_id",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "body_text",
                    "payload",
                )
            },
        ),
        (
            "Delivery Timeline",
            {
                "fields": (
                    "sent_at",
                    "delivered_at",
                    "read_at",
                    "received_at",
                )
            },
        ),
        (
            "Errors",
            {
                "fields": (
                    "error_code",
                    "error_message",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
