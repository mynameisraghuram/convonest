# backend/apps/messaging/services.py
from __future__ import annotations

from typing import Any, Dict, Optional
from django.utils import timezone

from .models import MessageLog, MessageType, MessageDirection, MessageStatus


def build_outbound_payload(
    *,
    to_phone: str,
    msg_type: MessageType | str,
    body_text: Optional[str] = None,
    media_url: Optional[str] = None,
    interactive: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
    waba_phone_number_id: Optional[str] = None,
    context_message_id: Optional[str] = None,
) -> Dict[str, Any]:
    if isinstance(msg_type, str):
        msg_type_enum = MessageType.__members__.get(msg_type, MessageType.UNKNOWN)
    else:
        msg_type_enum = msg_type

    payload: Dict[str, Any] = {
        "to": to_phone,
        "type": msg_type_enum.value.lower(),
        "messaging_product": "whatsapp",
    }

    if waba_phone_number_id:
        payload["phone_number_id"] = waba_phone_number_id

    if context_message_id:
        payload["context"] = {"message_id": context_message_id}

    if msg_type_enum == MessageType.TEXT:
        payload["text"] = {"body": body_text or ""}

    elif msg_type_enum in {
        MessageType.IMAGE,
        MessageType.VIDEO,
        MessageType.DOCUMENT,
        MessageType.AUDIO,
        MessageType.STICKER,
    }:
        payload[msg_type_enum.value.lower()] = {
            "link": media_url,
            "caption": body_text or "",
        }

    elif msg_type_enum == MessageType.LOCATION:
        payload["location"] = interactive or {}

    elif msg_type_enum == MessageType.INTERACTIVE:
        payload["interactive"] = interactive or {}

    elif msg_type_enum == MessageType.TEMPLATE:
        payload["template"] = template or {}
        payload["type"] = "template"

    else:
        payload["unknown"] = {
            "body": body_text or "",
            "extra": interactive or template or {},
        }

    return payload


def send_whatsapp_message(
    *,
    contact_phone: str,
    msg_type: MessageType | str = MessageType.TEXT,
    body_text: Optional[str] = None,
    media_url: Optional[str] = None,
    interactive: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
    waba_phone_number_id: Optional[str] = None,
    context_message_id: Optional[str] = None,
    contact_id: Optional[int] = None,
) -> MessageLog:
    payload = build_outbound_payload(
        to_phone=contact_phone,
        msg_type=msg_type,
        body_text=body_text,
        media_url=media_url,
        interactive=interactive,
        template=template,
        waba_phone_number_id=waba_phone_number_id,
        context_message_id=context_message_id,
    )

    msg_type_enum = (
        msg_type
        if isinstance(msg_type, MessageType)
        else MessageType.__members__.get(str(msg_type), MessageType.UNKNOWN)
    )

    return MessageLog.objects.create(
        direction=MessageDirection.OUTBOUND,
        msg_type=msg_type_enum,
        status=MessageStatus.QUEUED,
        contact_id=contact_id,
        contact_phone=contact_phone,
        waba_phone_number_id=waba_phone_number_id,
        body_text=body_text or "",
        payload=payload,
        sent_at=timezone.now(),
    )


def send_text_message_to_contact(*, contact, body_text: str, **kwargs) -> MessageLog:
    # Phase 1.1: log OUTBOUND (Meta call later)
    return send_whatsapp_message(
        contact_id=contact.id,
        contact_phone=contact.phone,
        msg_type=MessageType.TEXT,
        body_text=body_text,
        waba_phone_number_id=kwargs.get("waba_phone_number_id"),
        context_message_id=kwargs.get("context_message_id"),
    )
