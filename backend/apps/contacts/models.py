# backend/apps/contacts/models.py
from __future__ import annotations

from django.db import models
from django.core.validators import RegexValidator

from apps.core.models import TimeStampedModel


phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Phone number must be in E.164 format, e.g. +919876543210",
)


class Contact(TimeStampedModel):
    """
    Basic WhatsApp contact.

    Phase 1: single-tenant, keyed by phone.
    Later we can add Account / Tenant FK and more CRM fields.
    """

    full_name = models.CharField(max_length=191, blank=True)

    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[phone_validator],
        help_text="WhatsApp phone number in E.164 format, e.g. +919876543210",
        db_index=True,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="contacts",
        null=True,
        blank=True,
        db_index=True,
    )


    email = models.EmailField(blank=True, null=True, db_index=True)

    language = models.CharField(
        max_length=10,
        default="en",
        help_text="Preferred language code (e.g. en, en_US, hi).",
        db_index=True,
    )

    timezone = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Optional IANA timezone (e.g. Asia/Kolkata).",
    )

    # Consent & status flags
    is_opted_out = models.BooleanField(
        default=False,
        help_text="If true, do not send broadcast / marketing messages.",
    )
    is_blocked = models.BooleanField(
        default=False,
        help_text="If true, skip any automated messages to this contact.",
    )

    last_seen_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time we received a message from this contact.",
    )

    # Simple tags as list of strings (Postgres-only ArrayField is fine here)
    from django.contrib.postgres.fields import ArrayField  # type: ignore[attr-defined]

    tags = ArrayField(
        base_field=models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Segment tags, e.g. ['lead', 'webinar', 'hot'].",
    )

    extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Any extra metadata (utm, crm_id, etc.).",
    )

    class Meta:
        db_table = "contacts_contact"
        ordering = ["full_name", "phone"]
        indexes = [
            models.Index(fields=["is_opted_out", "is_blocked"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name or self.phone}"
