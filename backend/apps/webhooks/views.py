# backend/apps/webhooks/views.py
from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.contacts.services import touch_contact_from_inbound
from apps.messaging.models import MessageLog, MessageDirection, MessageStatus, MessageType


class WhatsAppWebhookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Meta webhook verification:
        ?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
        """
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        verify_token = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", None)

        if mode == "subscribe" and token and verify_token and token == verify_token:
            return Response(challenge, status=200)

        return Response({"detail": "Verification failed"}, status=403)

    def post(self, request):
        """
        Receives WhatsApp webhook payloads.
        For Phase-1: store inbound text + simple media metadata.
        """
        data = request.data or {}

        # Defensive parsing (Meta shape is nested)
        entries = data.get("entry") or []
        for entry in entries:
            changes = entry.get("changes") or []
            for change in changes:
                value = change.get("value") or {}
                messages = value.get("messages") or []
                contacts = value.get("contacts") or []

                # From contacts block we can pick profile name (optional)
                name_by_wa_id = {}
                for c in contacts:
                    wa_id = c.get("wa_id")
                    profile = c.get("profile") or {}
                    if wa_id:
                        name_by_wa_id[wa_id] = profile.get("name") or ""

                for msg in messages:
                    from_phone = msg.get("from")  # wa_id (digits), not +E164
                    msg_id = msg.get("id")
                    mtype = (msg.get("type") or "unknown").lower()

                    # store best-effort phone. You can normalize later.
                    phone_guess = f"+{from_phone}" if from_phone and not str(from_phone).startswith("+") else (from_phone or "")

                    body_text = ""
                    msg_type = MessageType.UNKNOWN
                    payload = msg

                    if mtype == "text":
                        body_text = ((msg.get("text") or {}).get("body")) or ""
                        msg_type = MessageType.TEXT
                    elif mtype == "image":
                        body_text = ((msg.get("image") or {}).get("caption")) or ""
                        msg_type = MessageType.IMAGE
                    elif mtype == "video":
                        body_text = ((msg.get("video") or {}).get("caption")) or ""
                        msg_type = MessageType.VIDEO
                    elif mtype == "audio":
                        msg_type = MessageType.AUDIO
                    elif mtype == "document":
                        body_text = ((msg.get("document") or {}).get("caption")) or ""
                        msg_type = MessageType.DOCUMENT
                    elif mtype == "interactive":
                        msg_type = MessageType.INTERACTIVE
                        body_text = "interactive"
                    else:
                        msg_type = MessageType.UNKNOWN

                    # Ensure contact exists / touched
                    full_name = name_by_wa_id.get(from_phone, "")
                    contact = touch_contact_from_inbound(
                        phone=phone_guess,
                        full_name=full_name or None,
                        language="en",
                        extra={"wa_id": from_phone} if from_phone else None,
                    )

                    MessageLog.objects.create(
                        direction=MessageDirection.INBOUND,
                        msg_type=msg_type,
                        status=MessageStatus.RECEIVED,
                        waba_message_id=msg_id,
                        contact=contact,
                        contact_phone=contact.phone,
                        body_text=body_text,
                        payload=payload,
                        received_at=timezone.now(),
                    )

        return Response({"ok": True}, status=200)
