# backend/apps/messaging/webhook_views.py
from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.contacts.services import touch_contact_from_inbound
from .models import MessageLog, MessageDirection, MessageStatus, MessageType


def _verify_token() -> str:
    return getattr(settings, "META_VERIFY_TOKEN", "")


@api_view(["GET"])
@permission_classes([AllowAny])
def whatsapp_webhook_verify(request):
    """
    Meta webhook verification:
    ?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token and token == _verify_token():
        return HttpResponse(challenge or "", content_type="text/plain")

    return HttpResponse("Verification failed", status=403)


@api_view(["POST"])
@permission_classes([AllowAny])
def whatsapp_webhook_receive(request):
    """
    Receives WhatsApp webhook payload and stores inbound messages.
    """
    root = request.data or {}
    entries = root.get("entry") or []
    saved = 0

    for entry in entries:
        for change in (entry.get("changes") or []):
            value = change.get("value") or {}

            phone_number_id = (value.get("metadata") or {}).get("phone_number_id")

            contacts_payload = value.get("contacts") or []
            name_by_waid = {}
            for c in contacts_payload:
                waid = c.get("wa_id")
                profile_name = (c.get("profile") or {}).get("name")
                if waid and profile_name:
                    name_by_waid[waid] = profile_name

            for m in (value.get("messages") or []):
                wa_from = m.get("from")  # wa_id digits
                wamid = m.get("id")
                mtype_raw = (m.get("type") or "text").upper()

                # best-effort E.164 (phase 0)
                contact_phone = ""
                if wa_from:
                    contact_phone = wa_from if str(wa_from).startswith("+") else f"+{wa_from}"

                # extract text / caption
                body_text = ""
                if mtype_raw == "TEXT":
                    body_text = (m.get("text") or {}).get("body") or ""
                else:
                    node = m.get((m.get("type") or "")) or {}
                    body_text = node.get("caption") or ""

                contact = None
                if contact_phone:
                    contact = touch_contact_from_inbound(
                        phone=contact_phone,
                        full_name=name_by_waid.get(wa_from),
                        language="en",
                        extra={"source": "whatsapp_webhook"},
                    )

                # map type to enum safely
                msg_type = mtype_raw if mtype_raw in MessageType.values else MessageType.UNKNOWN

                MessageLog.objects.create(
                    direction=MessageDirection.INBOUND,
                    msg_type=msg_type,
                    status=MessageStatus.RECEIVED,
                    waba_message_id=wamid,
                    contact=contact,
                    contact_phone=contact_phone or "",
                    waba_phone_number_id=phone_number_id,
                    body_text=body_text,
                    payload=m,
                    received_at=timezone.now(),
                )
                saved += 1

    return Response({"ok": True, "saved": saved})
