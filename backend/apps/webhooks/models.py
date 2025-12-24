# backend/apps/webhooks/models.py
from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.workspaces.models import Workspace


class WebhookProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"


class WhatsappWebhookConfig(TimeStampedModel):
    """
    Optional: per-workspace webhook verification config.
    You can keep using settings.META_VERIFY_TOKEN for now if you want global token.
    """

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="whatsapp_webhook_configs",
    )

    name = models.CharField(max_length=100, default="Default WhatsApp Webhook")

    verify_token = models.CharField(
        max_length=255,
        help_text="Verify token used in the webhook setup and GET challenge.",
    )

    phone_number_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Optional: Meta phone_number_id to link this config to a number.",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "webhooks_whatsapp_webhook_config"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "verify_token"],
                name="uq_webhookcfg_workspace_verify_token",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (workspace={self.workspace_id}, active={self.is_active})"


class WebhookEventLog(TimeStampedModel):
    """
    Stores incoming webhook events.
    - workspace can be NULL if we cannot route the event (missing/unknown phone_number_id).
    - dedupe enforced only when workspace is known.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="webhook_events",
        null=True,
        blank=True,
    )

    config = models.ForeignKey(
        WhatsappWebhookConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    provider = models.CharField(max_length=50, default="META_WHATSAPP", db_index=True)

    phone_number_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    dedupe_key = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Stable idempotency key to prevent duplicate processing.",
    )

    processing_status = models.CharField(
        max_length=20,
        choices=WebhookProcessingStatus.choices,
        default=WebhookProcessingStatus.PENDING,
        db_index=True,
    )

    error_message = models.TextField(blank=True, null=True)

    request_headers = models.JSONField(default=dict, blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    processed_at = models.DateTimeField(blank=True, null=True)
    delivery_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "webhooks_webhook_event_log"
        ordering = ["-created_at"]
        constraints = [
            # Enforce dedupe only when workspace is known.
            models.UniqueConstraint(
                fields=["workspace", "provider", "dedupe_key"],
                condition=Q(workspace__isnull=False),
                name="uq_webhookevent_workspace_provider_dedupe",
            )
        ]
        indexes = [
            models.Index(fields=["provider", "created_at"]),
            models.Index(fields=["processing_status", "created_at"]),
            models.Index(fields=["phone_number_id", "created_at"]),
        ]

    def mark_processed(self) -> None:
        self.processing_status = WebhookProcessingStatus.PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=["processing_status", "processed_at", "updated_at"])

    def mark_failed(self, error: str) -> None:
        self.processing_status = WebhookProcessingStatus.FAILED
        self.error_message = error
        self.processed_at = timezone.now()
        self.save(update_fields=["processing_status", "error_message", "processed_at", "updated_at"])

    def __str__(self) -> str:
        return f"WebhookEventLog(id={self.id}, workspace={self.workspace_id}, status={self.processing_status})"
