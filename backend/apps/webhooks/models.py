
# backend/apps/webhooks/models.py
from django.db import models

from apps.core.models import TimeStampedModel


class WebhookProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"


class WhatsappWebhookConfig(TimeStampedModel):
    """
    Stores config needed for WhatsApp Cloud API webhook verification.

    Right now: just verify_token + is_active.
    Later you can link this to Account / WhatsApp Business Number.
    """

    name = models.CharField(max_length=100, default="Default WhatsApp Webhook")
    verify_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Verify token used in the webhook setup and GET challenge.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "webhooks_whatsapp_webhook_config"

    def __str__(self) -> str:
        return f"{self.name} (active={self.is_active})"


class WebhookEventLog(TimeStampedModel):
    """
    Stores every incoming webhook event from WhatsApp.

    We keep the raw payload + minimal metadata so we can reprocess if needed.
    """

    # Optional: you can later link this to WhatsappWebhookConfig or Account.
    config = models.ForeignKey(
        WhatsappWebhookConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    processing_status = models.CharField(
        max_length=20,
        choices=WebhookProcessingStatus.choices,
        default=WebhookProcessingStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)

    # Raw HTTP info
    request_headers = models.JSONField(default=dict, blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw JSON body received from WhatsApp.",
    )

    processed_at = models.DateTimeField(blank=True, null=True)
    delivery_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "webhooks_webhook_event_log"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"WebhookEventLog(id={self.id}, status={self.processing_status})"
