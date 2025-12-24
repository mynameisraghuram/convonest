from __future__ import annotations

from rest_framework import serializers
from apps.contacts.models import Contact
from .models import MessageLog, MessageDirection


class MessageLogSerializer(serializers.ModelSerializer):
    contact_full_name = serializers.CharField(source="contact.full_name", read_only=True)

    class Meta:
        model = MessageLog
        fields = [
            "id",
            "direction",
            "msg_type",
            "status",
            "contact",
            "contact_full_name",
            "contact_phone",
            "body_text",
            "waba_message_id",
            "waba_phone_number_id",
            "sent_at",
            "delivered_at",
            "read_at",
            "received_at",
            "created_at",
        ]
        read_only_fields = fields


class ConversationSerializer(serializers.Serializer):
    contact_id = serializers.IntegerField()
    contact_full_name = serializers.CharField()
    contact_phone = serializers.CharField()
    last_message_text = serializers.CharField()
    last_message_at = serializers.DateTimeField()
    last_direction = serializers.ChoiceField(choices=MessageDirection.choices)
    unread_count = serializers.IntegerField()


class SendMessageSerializer(serializers.Serializer):
    contact_id = serializers.IntegerField()
    body_text = serializers.CharField(max_length=4096)

    def validate_contact_id(self, value):
        if not Contact.objects.filter(id=value).exists():
            raise serializers.ValidationError("Contact not found.")
        return value


class MarkReadSerializer(serializers.Serializer):
    contact_id = serializers.IntegerField()

    def validate_contact_id(self, value):
        if not Contact.objects.filter(id=value).exists():
            raise serializers.ValidationError("Contact not found.")
        return value
