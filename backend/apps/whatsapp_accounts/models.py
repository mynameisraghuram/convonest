# backend/apps/whatsapp_accounts/models.py

from django.db import models
from django.utils import timezone


class WhatsappBusinessAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=64)  # WABA_ID
    name = models.CharField(max_length=255, blank=True)
    meta_business_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=64, blank=True)
    limits = models.JSONField(default=dict, blank=True)
    meta_raw = models.JSONField(default=dict, blank=True)

    # NOTE: "is_connected" on WABA object can be misleading in multi-tenant SaaS.
    # Keep it if you want, but treat "WhatsappConnection.is_active" as truth.
    is_connected = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or self.id}"


class WhatsappPhoneNumber(models.Model):
    id = models.CharField(primary_key=True, max_length=64)  # PHONE_NUMBER_ID
    waba = models.ForeignKey(
        WhatsappBusinessAccount,
        related_name="phone_numbers",
        on_delete=models.CASCADE,
    )

    e164_number = models.CharField(max_length=32, help_text="+911234567890", blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True, default="")
    display_name_status = models.CharField(max_length=32, default="UNKNOWN")
    rejection_reason = models.TextField(blank=True, default="")

    registered = models.BooleanField(default=False)
    two_step_enabled = models.BooleanField(default=False)
    test_number = models.BooleanField(default=False)

    oba_status = models.CharField(max_length=32, default="UNKNOWN")
    profile = models.JSONField(default=dict, blank=True)
    meta_raw = models.JSONField(default=dict, blank=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["waba"]),
            models.Index(fields=["e164_number"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.e164_number})"


class WhatsappConnection(models.Model):
    """
    This is the REAL "integration" object in a SaaS:
    Workspace owns a token + selected WABA + selected phone number.
    """

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="whatsapp_connections",
    )

    waba = models.ForeignKey(
        WhatsappBusinessAccount,
        on_delete=models.CASCADE,
        related_name="connections",
    )

    phone_number = models.ForeignKey(
        WhatsappPhoneNumber,
        on_delete=models.CASCADE,
        related_name="connections",
    )

    # Token from OAuth (ideally long-lived).
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Webhook verification token (your server checks hub.verify_token against this)
    verify_token = models.CharField(max_length=128)

    # Optional: useful for audits/debugging OAuth
    meta_user_id = models.CharField(max_length=64, blank=True, default="")
    scopes = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)

    connected_at = models.DateTimeField(auto_now_add=True)
    last_webhook_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # 1 workspace -> 1 active connection (simple MVP rule)
            models.UniqueConstraint(
                fields=["workspace"],
                condition=models.Q(is_active=True),
                name="uniq_active_whatsapp_connection_per_workspace",
            ),
            # same phone number can't be connected twice within same workspace
            models.UniqueConstraint(
                fields=["workspace", "phone_number"],
                name="uniq_workspace_phone_number_connection",
            ),
        ]
        indexes = [
            # webhook lookup: phone_number_id -> active connection
            models.Index(fields=["phone_number", "is_active"]),
            models.Index(fields=["workspace", "is_active"]),
        ]

    def __str__(self):
        return f"{self.workspace_id} → {self.phone_number_id}"



class WhatsappContact(models.Model):
    """
    Must be workspace-scoped to avoid collisions across tenants.
    """
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="whatsapp_contacts",
        null=True, blank=True,
    )

    bsuid = models.CharField(max_length=128)  # no longer globally unique
    phone = models.CharField(max_length=32, blank=True, null=True)
    wa_username = models.CharField(max_length=64, blank=True, null=True)

    meta_raw = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace", "bsuid"], name="uniq_workspace_bsuid"),
        ]
        indexes = [
            models.Index(fields=["workspace", "phone"]),
            models.Index(fields=["workspace", "bsuid"]),
        ]

    def __str__(self):
        return self.wa_username or self.phone or self.bsuid


class WhatsappConversation(models.Model):
    CATEGORY_CHOICES = [
        ("MARKETING", "Marketing"),
        ("UTILITY", "Utility"),
        ("AUTHENTICATION", "Authentication"),
        ("SERVICE", "Service"),
    ]

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="whatsapp_conversations",
        null=True, blank=True,
    )

    contact = models.ForeignKey(
        WhatsappContact, related_name="conversations", on_delete=models.CASCADE
    )
    phone_number = models.ForeignKey(
        WhatsappPhoneNumber, related_name="conversations", on_delete=models.CASCADE
    )

    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    opened_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    meta_raw = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "phone_number"]),
            models.Index(fields=["workspace", "contact"]),
        ]

    def __str__(self):
        return f"{self.category} with {self.contact} on {self.phone_number}"


class WhatsappQrCode(models.Model):
    id = models.CharField(primary_key=True, max_length=128)  # Meta QRD ID

    waba = models.ForeignKey(
        WhatsappBusinessAccount, related_name="qr_codes", on_delete=models.CASCADE
    )
    phone_number = models.ForeignKey(
        WhatsappPhoneNumber, related_name="qr_codes", on_delete=models.CASCADE
    )

    # optional but very useful: who created this QR inside your SaaS
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="whatsapp_qr_codes",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=255)
    deep_link = models.URLField()
    image_url = models.URLField()
    default_message = models.CharField(max_length=512, blank=True, default="")
    meta_raw = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
