# backend/apps/contacts/views.py
from __future__ import annotations

import csv
import io
from typing import List

from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    Basic CRUD API for contacts.

    Phase 1: simple auth-based protection.
    Extra:
      - POST /api/contacts/bulk/          → bulk JSON create
      - POST /api/contacts/import-csv/   → import contacts from CSV file
      - GET  /api/contacts/export-csv/   → export all contacts as CSV
    """

    queryset = Contact.objects.all().order_by("full_name", "phone")
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]


    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "phone", "email", "tags"]
    ordering_fields = ["full_name", "phone", "created_at"]
    ordering = ["full_name"]

    # -------- BULK JSON CREATE --------
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request, *args, **kwargs):
        """
        Accepts a list of contact objects and creates them in one shot.

        Payload:
        [
          {"full_name": "Alice", "phone": "+9198...", "email": "..."},
          {"full_name": "Bob", "phone": "+91...", "tags": ["lead", "webinar"]}
        ]
        """

        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of objects."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            contacts = serializer.save()

        return Response(
            self.get_serializer(contacts, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    # -------- CSV IMPORT --------
    @action(
        detail=False,
        methods=["post"],
        url_path="import-csv",
        parser_classes=[MultiPartParser],
    )
    def import_csv(self, request, *args, **kwargs):
        """
        Import contacts from an uploaded CSV file.

        Expected columns (header row, case-insensitive):
          full_name, phone, email, language, timezone, tags

        tags: optional, comma-separated (e.g. "lead, webinar").
        """

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"detail": "No file uploaded with key 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded = file_obj.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "Unable to decode CSV file as UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(decoded))
        rows: List[dict] = []
        for row in reader:
            # normalise keys to lowercase
            row_norm = {k.lower(): v for k, v in row.items()}

            tags_raw = (row_norm.get("tags") or "").strip()
            tags = (
                [t.strip() for t in tags_raw.split(",") if t.strip()]
                if tags_raw
                else []
            )

            rows.append(
                {
                    "full_name": row_norm.get("full_name") or "",
                    "phone": row_norm.get("phone") or "",
                    "email": row_norm.get("email") or None,
                    "language": row_norm.get("language") or "en",
                    "timezone": row_norm.get("timezone") or None,
                    "tags": tags,
                    # you could also map is_opted_out, etc.
                }
            )

        serializer = self.get_serializer(data=rows, many=True)
        serializer.is_valid(raise_exception=True)

        # upsert semantics: if phone exists, update; else, create
        created_or_updated: List[Contact] = []
        with transaction.atomic():
            for item in serializer.validated_data:
                phone = item["phone"]
                obj, _created = Contact.objects.update_or_create(
                    phone=phone,
                    defaults=item,
                )
                created_or_updated.append(obj)

        return Response(
            self.get_serializer(created_or_updated, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    # -------- CSV EXPORT --------
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request, *args, **kwargs):
        """
        Export all contacts as CSV.
        """

        contacts = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="contacts.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "full_name",
                "phone",
                "email",
                "language",
                "timezone",
                "is_opted_out",
                "is_blocked",
                "tags",
                "created_at",
                "updated_at",
            ]
        )

        for c in contacts:
            writer.writerow(
                [
                    c.full_name,
                    c.phone,
                    c.email or "",
                    c.language,
                    c.timezone or "",
                    c.is_opted_out,
                    c.is_blocked,
                    ",".join(c.tags or []),
                    c.created_at.isoformat(),
                    c.updated_at.isoformat(),
                ]
            )

        return response
