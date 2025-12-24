# backend/apps/messaging/models.py
from django.db import models
from apps.contacts.models import Contact 

from apps.core.models import TimeStampedModel


class MessageDirection(models.TextChoices):
    INBOUND = "IN", "Inbound"      # from WhatsApp user → your platform
    OUTBOUND = "OUT", "Outbound"   # from your platform → WhatsApp user


class MessageType(models.TextChoices):
    TEXT = "TEXT", "Text"
    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"
    AUDIO = "AUDIO", "Audio"
    DOCUMENT = "DOCUMENT", "Document"
    STICKER = "STICKER", "Sticker"
    LOCATION = "LOCATION", "Location"
    INTERACTIVE = "INTERACTIVE", "Interactive"   # buttons, lists, etc.
    TEMPLATE = "TEMPLATE", "Template"
    UNKNOWN = "UNKNOWN", "Unknown"


class MessageStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"          # created in system, not yet sent
    SENT = "SENT", "Sent"                # accepted by Meta API
    DELIVERED = "DELIVERED", "Delivered" # delivered to user
    READ = "READ", "Read"                # read by user
    RECEIVED = "RECEIVED", "Received"    # inbound message saved
    FAILED = "FAILED", "Failed"          # send failed


class MessageLog(TimeStampedModel):
    """
    Normalised store for all WhatsApp messages (inbound + outbound).

    Later we will add FKs to:
      - Account / Tenant
      - Contact
      - WhatsappBusinessNumber

    For Phase-0 we keep it phone-based and JSON-based so you can move fast.
    """

    direction = models.CharField(
        max_length=3,
        choices=MessageDirection.choices,
        db_index=True,
    )

    msg_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.QUEUED,
        db_index=True,
    )

    # WhatsApp identifiers
    waba_message_id = models.CharField(
        max_length=191,
        blank=True,
        null=True,
        help_text="WhatsApp Business API message ID (wamid).",
        db_index=True,
    )

    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
        help_text="FK to Contact (if available).",
    )

    context_message_id = models.CharField(
        max_length=191,
        blank=True,
        null=True,
        help_text="Reply-to message ID (if this message is a reply).",
    )

    # Phone info – we’ll link to Contact model later
    contact_phone = models.CharField(
        max_length=20,
        help_text="E.164 formatted phone number of the WhatsApp user.",
        db_index=True,
    )

    waba_phone_number_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="The phone_number_id used to send/receive this message.",
    )

    # Human-readable text (if applicable)
    body_text = models.TextField(
        blank=True,
        help_text="Primary text body if present (message body, caption, etc.).",
    )

    # Full raw payload as JSON – keeps everything from Meta
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw WhatsApp message payload (normalized or original).",
    )

    # Error info for failed sends
    error_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Error code returned by Meta (if any).",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message returned by Meta (if any).",
    )

    # Timeline fields (optional but very useful for analytics)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    received_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="For inbound messages, when we stored it.",
    )

    class Meta:
        db_table = "messaging_message_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["direction", "status"]),
            models.Index(fields=["contact_phone", "created_at"]),
            models.Index(fields=["waba_message_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_direction_display()} {self.msg_type} to {self.contact_phone} ({self.status})"
