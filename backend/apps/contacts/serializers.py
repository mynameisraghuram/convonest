# backend/apps/contacts/serializers.py

from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "full_name",
            "phone",
            "email",
            "language",
            "timezone",
            "is_opted_out",
            "is_blocked",
            "last_seen_at",
            "tags",
            "extra",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_seen_at"]

    def validate_phone(self, value: str) -> str:
        # Normalize small things: trim spaces
        return value.strip()

    def validate_tags(self, value):
        # Ensure list[str], trimmed, unique, max 50 chars
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("tags must be a list of strings")
        cleaned = []
        seen = set()
        for t in value:
            if not isinstance(t, str):
                continue
            t = t.strip()
            if not t:
                continue
            if len(t) > 50:
                raise serializers.ValidationError("tag too long (max 50 chars)")
            if t.lower() in seen:
                continue
            seen.add(t.lower())
            cleaned.append(t)
        return cleaned

