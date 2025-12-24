# backend/apps/webhooks/tasks.py

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from celery import shared_task
from django.utils import timezone

from .models import WebhookEventLog, WebhookProcessingStatus

from apps.contacts.services import touch_contact_from_inbound
from apps.messaging.models import (
    MessageLog,
    MessageType,
    MessageDirection,
    MessageStatus,               
     
)

logger = logging.getLogger(__name__)


def _normalize_phone(raw: Optional[str]) -> str:
    """
    Very simple normaliser for WhatsApp numbers.

    Cloud API usually sends '919876543210' (no +).
    For now we just ensure it's prefixed with +.
    """
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("+"):
        return raw
    return f"+{raw}"


def _map_msg_type(type_str: Optional[str]) -> MessageType:
    """
    Map WhatsApp Cloud API 'type' (text, image, audio, etc.)
    to our internal MessageType enum.
    """
    t = (type_str or "").upper()

    mapping = {
        "TEXT": MessageType.TEXT,
        "IMAGE": MessageType.IMAGE,
        "VIDEO": MessageType.VIDEO,
        "AUDIO": MessageType.AUDIO,
        "DOCUMENT": MessageType.DOCUMENT,
        "STICKER": MessageType.STICKER,
        "LOCATION": MessageType.LOCATION,
        "INTERACTIVE": MessageType.INTERACTIVE,
        "TEMPLATE": MessageType.TEMPLATE,
    }
    return mapping.get(t, MessageType.UNKNOWN)


def _extract_body_text(msg: Dict[str, Any]) -> str:
    """
    Extract human-readable text from a WhatsApp message payload.
    """
    msg_type = msg.get("type")

    if msg_type == "text":
        return (msg.get("text") or {}).get("body", "") or ""

    if msg_type in {"image", "video", "document", "audio"}:
        media = msg.get(msg_type) or {}
        caption = media.get("caption")
        if caption:
            return caption
        return f"[{msg_type} message]"

    if msg_type == "location":
        loc = msg.get("location") or {}
        name = loc.get("name") or ""
        address = loc.get("address") or ""
        coords = f"{loc.get('latitude')},{loc.get('longitude')}"
        return f"[location] {name} {address} ({coords})".strip()

    if msg_type == "interactive":
        interactive = msg.get("interactive") or {}
        itype = interactive.get("type")
        if itype == "button_reply":
            reply = interactive.get("button_reply") or {}
            return f"[button reply] {reply.get('title', '')}"
        if itype == "list_reply":
            reply = interactive.get("list_reply") or {}
            return f"[list reply] {reply.get('title', '')}"
        return "[interactive message]"

    if msg_type == "template":
        return "[template message]"

    return "[unknown message type]"


@shared_task
def process_webhook_event(event_id: int) -> None:
    """
    Processes a single WebhookEventLog from WhatsApp Cloud API:

      - Parses entry[] / changes[] / value
      - For each inbound message:
          * Normalise phone
          * Upsert Contact (touch_contact_from_inbound)
          * Create MessageLog(direction=IN, status=RECEIVED)
    """
    try:
        event = WebhookEventLog.objects.get(id=event_id)
    except WebhookEventLog.DoesNotExist:
        logger.warning("WebhookEventLog %s does not exist", event_id)
        return

    event.delivery_attempts += 1

    try:
        payload: Dict[str, Any] = event.payload or {}
        entries: List[Dict[str, Any]] = payload.get("entry") or []

        if not entries:
            logger.info("WebhookEventLog %s has no 'entry'; skipping.", event_id)
            event.processing_status = WebhookProcessingStatus.PROCESSED
            event.processed_at = timezone.now()
            event.error_message = ""
            event.save(
                update_fields=[
                    "processing_status",
                    "processed_at",
                    "error_message",
                    "delivery_attempts",
                ]
            )
            return

        for entry in entries:
            changes: List[Dict[str, Any]] = entry.get("changes") or []
            for change in changes:
                value: Dict[str, Any] = change.get("value") or {}

                metadata = value.get("metadata") or {}
                waba_phone_number_id = metadata.get("phone_number_id")

                wa_contacts = value.get("contacts") or []
                wa_profile_name = ""
                wa_contact_wa_id = None
                if wa_contacts:
                    c0 = wa_contacts[0]
                    wa_profile_name = (c0.get("profile") or {}).get("name", "")
                    wa_contact_wa_id = c0.get("wa_id")

                messages = value.get("messages") or []
                if not messages:
                    continue

                for msg in messages:
                    # 1) Basic identifiers
                    wa_from = msg.get("from")  # e.g. "919876543210"
                    if not wa_from:
                        logger.info("Message without 'from' in event %s; skipping.", event_id)
                        continue

                    normalized_phone = _normalize_phone(wa_from)
                    profile_name = wa_profile_name or (msg.get("profile") or {}).get("name", "")
                    wa_msg_id = msg.get("id")

                    # 2) Ensure Contact exists
                    contact = touch_contact_from_inbound(
                        phone=normalized_phone,
                        full_name=profile_name,
                        extra={"wa_id": wa_contact_wa_id or wa_msg_id},
                    )

                    # 3) Message content
                    msg_type = _map_msg_type(msg.get("type"))
                    body_text = _extract_body_text(msg)

                    # 4) Create MessageLog (inbound)
                    MessageLog.objects.create(
                        direction=MessageDirection.IN,         # 👈 IN (not INBOUND)
                        msg_type=msg_type,
                        status=MessageStatus.RECEIVED,        # 👈 RECEIVED for inbound
                        contact=contact,
                        contact_phone=normalized_phone,
                        waba_phone_number_id=waba_phone_number_id,
                        waba_message_id=wa_msg_id,
                        context_message_id=(msg.get("context") or {}).get("id"),
                        body_text=body_text,
                        payload=msg,
                        received_at=timezone.now(),
                    )

        event.processing_status = WebhookProcessingStatus.PROCESSED
        event.processed_at = timezone.now()
        event.error_message = ""
        event.save(
            update_fields=[
                "processing_status",
                "processed_at",
                "error_message",
                "delivery_attempts",
            ]
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Error processing webhook event %s: %s", event_id, exc)
        event.processing_status = WebhookProcessingStatus.FAILED
        event.error_message = str(exc)
        event.processed_at = timezone.now()
        event.save(
            update_fields=[
                "processing_status",
                "error_message",
                "processed_at",
                "delivery_attempts",
            ]
        )
