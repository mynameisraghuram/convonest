from rest_framework import serializers
from .models import Template


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = [
            "id",
            "name",
            "language",
            "category",
            "subtype",
            "components",
            "status",
            "external_id",
            "rejection_reason",
            "auth_type",
            "ttl_seconds",
            "quality_rating",
            "messaging_limit_tier",
            "is_paused",
            "source",
            "group_key",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "external_id",
            "rejection_reason",
            "quality_rating",
            "messaging_limit_tier",
            "is_paused",
            "source",
            "created_at",
            "updated_at",
        ]


class TemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = [
            "id",
            "name",
            "language",
            "category",
            "subtype",
            "components",
            "auth_type",
            "ttl_seconds",
            "group_key",
        ]
