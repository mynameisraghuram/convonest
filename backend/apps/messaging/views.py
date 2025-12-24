from __future__ import annotations

from django.db.models import Max, Count, Q
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.contacts.models import Contact
from .models import MessageLog, MessageDirection, MessageStatus
from .serializers import (
    MessageLogSerializer,
    ConversationSerializer,
    SendMessageSerializer,
    MarkReadSerializer,
)
from .services import send_text_message_to_contact


class InboxConversationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /api/messaging/inbox/conversations/
    One row per contact with:
      - last message
      - last direction
      - unread inbound count
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        qs = (
            MessageLog.objects.exclude(contact__isnull=True)
            .values("contact_id", "contact__full_name", "contact_phone")
            .annotate(
                last_message_at=Max("created_at"),
                last_message_id=Max("id"),
                unread_count=Count(
                    "id",
                    filter=Q(direction=MessageDirection.INBOUND)
                    & ~Q(status=MessageStatus.READ),
                ),
            )
            .order_by("-last_message_at")
        )

        last_ids = [row["last_message_id"] for row in qs if row["last_message_id"]]
        last_messages = {m.id: m for m in MessageLog.objects.filter(id__in=last_ids)}

        conversations = []
        for row in qs:
            last_msg = last_messages.get(row["last_message_id"])
            if not last_msg:
                continue

            conversations.append(
                {
                    "contact_id": row["contact_id"],
                    "contact_full_name": row["contact__full_name"] or "",
                    "contact_phone": row["contact_phone"],
                    "last_message_text": last_msg.body_text or "",
                    "last_message_at": row["last_message_at"],
                    "last_direction": last_msg.direction,
                    "unread_count": row["unread_count"],
                }
            )

        return Response(ConversationSerializer(conversations, many=True).data)


class InboxMessageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/messaging/inbox/messages/?contact=<id>
    POST /api/messaging/inbox/messages/send/
    POST /api/messaging/inbox/messages/mark_read/
    """

    serializer_class = MessageLogSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = MessageLog.objects.all().select_related("contact").order_by("created_at")

        contact_id = self.request.query_params.get("contact")
        if contact_id:
            try:
                contact_id_int = int(contact_id)
            except (TypeError, ValueError):
                return MessageLog.objects.none()
            qs = qs.filter(contact_id=contact_id_int)

        return qs

    @action(detail=False, methods=["post"], url_path="send")
    def send_message(self, request, *args, **kwargs):
        """
        POST /api/messaging/inbox/messages/send/
        {
          "contact_id": 3,
          "body_text": "hi"
        }
        """
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_id = serializer.validated_data["contact_id"]
        body_text = serializer.validated_data["body_text"]

        contact = Contact.objects.get(id=contact_id)

        msg_log = send_text_message_to_contact(contact=contact, body_text=body_text)

        return Response(MessageLogSerializer(msg_log).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="mark_read")
    def mark_read(self, request, *args, **kwargs):
        """
        POST /api/messaging/inbox/messages/mark_read/
        { "contact_id": 3 }
        Marks inbound messages as READ for this contact.
        """
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_id = serializer.validated_data["contact_id"]

        now = timezone.now()

        updated = (
            MessageLog.objects.filter(
                contact_id=contact_id,
                direction=MessageDirection.INBOUND,  # ✅ correct enum
            )
            .exclude(status=MessageStatus.READ)
            .update(status=MessageStatus.READ, read_at=now)
        )

        return Response({"updated": updated}, status=status.HTTP_200_OK)
