from rest_framework import serializers
from .models import (
    WhatsappBusinessAccount,
    WhatsappPhoneNumber,
    WhatsappContact,
    WhatsappConversation,
    WhatsappQrCode,
    WhatsappConnection,
)


class WhatsappBusinessAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappBusinessAccount
        fields = "__all__"


class WhatsappPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappPhoneNumber
        fields = "__all__"


class WhatsappConnectionSerializer(serializers.ModelSerializer):
    # Helpful read-only nested details (UI-friendly)
    waba = WhatsappBusinessAccountSerializer(read_only=True)
    phone_number = WhatsappPhoneNumberSerializer(read_only=True)

    # Write fields
    waba_id = serializers.CharField(write_only=True, required=True)
    phone_number_id = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = WhatsappConnection
        fields = [
            "id",
            "workspace",
            "waba",
            "phone_number",
            "waba_id",
            "phone_number_id",
            "access_token",
            "token_expires_at",
            "verify_token",
            "meta_user_id",
            "scopes",
            "is_active",
            "connected_at",
            "last_webhook_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["workspace", "connected_at", "last_webhook_at", "created_at", "updated_at"]

    def validate(self, attrs):
        # Extra sanity checks can go here later (token presence, etc.)
        return attrs


class WhatsappContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappContact
        fields = "__all__"
        read_only_fields = ["workspace"]


class WhatsappConversationSerializer(serializers.ModelSerializer):
    contact = WhatsappContactSerializer(read_only=True)
    phone_number = WhatsappPhoneNumberSerializer(read_only=True)

    class Meta:
        model = WhatsappConversation
        fields = "__all__"
        read_only_fields = ["workspace"]


class WhatsappQrCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappQrCode
        fields = "__all__"
