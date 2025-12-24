#backend/apps/templates/models.py

from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class TemplateCategory(models.TextChoices):
    MARKETING = "MARKETING", "Marketing"
    UTILITY = "UTILITY", "Utility"
    AUTHENTICATION = "AUTHENTICATION", "Authentication"


class TemplateStatus(models.TextChoices):
    # include DRAFT because local creation needs it
    DRAFT = "DRAFT", "Draft"
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    DISABLED = "DISABLED", "Disabled"
    IN_APPEAL = "IN_APPEAL", "In appeal"


class TemplateAuthType(models.TextChoices):
    NONE = "NONE", "None"
    COPY_CODE = "COPY_CODE", "Copy code"
    ONE_TAP = "ONE_TAP", "One-tap"
    ZERO_TAP = "ZERO_TAP", "Zero-tap"


class TemplateSource(models.TextChoices):
    META_SYNC = "META_SYNC", "Synced from Meta"
    LOCAL = "LOCAL", "Created in ConvoNest"


class Template(TimeStampedModel):
    """
    Normalised WhatsApp template model mirroring Meta metadata.
    """

    name = models.CharField(max_length=191, db_index=True)

    # Meta's template identifier + namespace (if available)
    external_id = models.CharField(
        max_length=191,
        blank=True,
        null=True,
        help_text="ID from Meta Business / Cloud API, if synced.",
        db_index=True,
    )
    namespace = models.CharField(
        max_length=191,
        blank=True,
        null=True,
        help_text="Template namespace from Meta (if provided).",
    )

    category = models.CharField(max_length=32, choices=TemplateCategory.choices, db_index=True)

    subtype = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Optional subtype: COUPON, CATALOG, MEDIA_CAROUSEL, CALL_PERMISSION, etc.",
        db_index=True,
    )

    language = models.CharField(
        max_length=10,
        default="en",
        help_text="BCP-47 language code (e.g. en, en_US, hi).",
        db_index=True,
    )

    auth_type = models.CharField(
        max_length=32,
        choices=TemplateAuthType.choices,
        default=TemplateAuthType.NONE,
        help_text="For authentication templates: COPY_CODE, ONE_TAP, ZERO_TAP.",
    )

    body_text = models.TextField(blank=True, help_text="Primary body text with variables (for search/preview).")

    # IMPORTANT: store Meta components array OR our own structure.
    # We'll accept either in API; submission will normalize to Meta format.
    components = models.JSONField(default=dict, blank=True)

    variable_count = models.PositiveIntegerField(default=0)

    quality_rating = models.CharField(max_length=32, blank=True, null=True)
    messaging_limit_tier = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(
        max_length=32,
        choices=TemplateStatus.choices,
        default=TemplateStatus.PENDING,
        db_index=True,
    )

    is_paused = models.BooleanField(default=False)

    ttl_seconds = models.PositiveIntegerField(default=0)

    # Grouping & versioning
    group_key = models.CharField(max_length=191, blank=True, null=True, db_index=True)
    previous_template = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_versions",
    )

    source = models.CharField(max_length=32, choices=TemplateSource.choices, default=TemplateSource.META_SYNC)

    # meta sync extras
    meta_raw = models.JSONField(default=dict, blank=True)

    # store last rejection reason cleanly for UX
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "templates_template"
        ordering = ["name", "language"]
        unique_together = ("name", "language")
        indexes = [
            models.Index(fields=["category", "language"]),
            models.Index(fields=["status", "quality_rating"]),
            models.Index(fields=["group_key", "language"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.language}] ({self.category})"


class TemplateButtonType(models.TextChoices):
    QUICK_REPLY = "QUICK_REPLY", "Quick reply"
    URL = "URL", "URL"
    PHONE = "PHONE", "Phone"
    COPY_CODE = "COPY_CODE", "Copy code"
    ONE_TAP = "ONE_TAP", "One-tap"
    OTHER = "OTHER", "Other"


class TemplateButtonConfig(TimeStampedModel):
    """
    Convenience denormalized button info for querying.
    """

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="buttons")
    index = models.PositiveIntegerField()

    button_type = models.CharField(max_length=32, choices=TemplateButtonType.choices, default=TemplateButtonType.OTHER)

    text = models.CharField(max_length=191)
    url = models.CharField(max_length=500, blank=True, null=True)
    phone_number = models.CharField(max_length=32, blank=True, null=True)

    # FIX: services.py was trying to write these
    payload = models.CharField(max_length=500, blank=True, null=True)
    extra = models.JSONField(default=dict, blank=True)
