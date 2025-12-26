# backend/apps/webhooks/tasks.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from celery import shared_task
from django.db import transaction
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
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("+"):
        return raw
    return f"+{raw}"


def _map_msg_type(type_str: Optional[str]) -> MessageType:
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


def _extract_value_blocks(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return a list of value dicts for each entry/change.
    """
    entries: List[Dict[str, Any]] = payload.get("entry") or []
    values: List[Dict[str, Any]] = []
    for entry in entries:
        for change in (entry.get("changes") or []):
            values.append(change.get("value") or {})
    return values


def _map_meta_status(status: str) -> Optional[MessageStatus]:
    s = (status or "").upper()
    mapping = {
        "SENT": getattr(MessageStatus, "SENT", None),
        "DELIVERED": getattr(MessageStatus, "DELIVERED", None),
        "READ": getattr(MessageStatus, "READ", None),
        "FAILED": getattr(MessageStatus, "FAILED", None),
    }
    return mapping.get(s)


def _ts_to_dt(ts: Optional[str]) -> Optional[timezone.datetime]:
    """
    Meta sends timestamps as string seconds-since-epoch.
    Convert to timezone-aware datetime.
    """
    if not ts:
        return None
    try:
        return timezone.datetime.fromtimestamp(
            int(ts),
            tz=timezone.get_current_timezone(),
        )
    except Exception:
        return None


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 8},
)
def process_webhook_event(self, event_id: int) -> None:
    try:
        event = WebhookEventLog.objects.select_related("workspace").get(id=event_id)
    except WebhookEventLog.DoesNotExist:
        logger.warning("WebhookEventLog %s does not exist", event_id)
        return

    # Count attempts
    event.delivery_attempts = (event.delivery_attempts or 0) + 1
    event.save(update_fields=["delivery_attempts", "updated_at"])

    # If already processed, exit safely
    if event.processing_status == WebhookProcessingStatus.PROCESSED:
        return

    # Workspace is required to write messages/contacts in a multi-tenant system
    if event.workspace is None:
        event.processing_status = WebhookProcessingStatus.FAILED
        event.error_message = "Unroutable webhook event: workspace is NULL"
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "error_message", "processed_at", "updated_at"])
        return

    try:
        payload: Dict[str, Any] = event.payload or {}
        values = _extract_value_blocks(payload)

        if not values:
            event.processing_status = WebhookProcessingStatus.PROCESSED
            event.processed_at = timezone.now()
            event.error_message = ""
            event.save(update_fields=["processing_status", "processed_at", "error_message", "updated_at"])
            return

        with transaction.atomic():
            for value in values:
                metadata = value.get("metadata") or {}
                # Prefer metadata phone_number_id; fall back to what's stored on event (if you have it)
                waba_phone_number_id = metadata.get("phone_number_id") or getattr(event, "phone_number_id", None)

                # contacts block (profile name + wa_id)
                wa_contacts = value.get("contacts") or []
                wa_profile_name = ""
                wa_contact_wa_id = None
                if wa_contacts:
                    c0 = wa_contacts[0]
                    wa_profile_name = (c0.get("profile") or {}).get("name", "")
                    wa_contact_wa_id = c0.get("wa_id")

                # 1) inbound messages
                messages = value.get("messages") or []
                for msg in messages:
                    wa_from = msg.get("from")  # "9198..."
                    if not wa_from:
                        continue

                    normalized_phone = _normalize_phone(wa_from)
                    profile_name = wa_profile_name or (msg.get("profile") or {}).get("name", "")
                    wa_msg_id = msg.get("id")
                    if not wa_msg_id:
                        # Without message id, we can't dedupe reliably; skip to avoid duplicates.
                        logger.warning("Inbound message missing id, event_id=%s", event_id)
                        continue

                    # Contact upsert (workspace-scoped)
                    # IMPORTANT: wa_id should be wa_contact_wa_id or wa_from (NOT message id)
                    contact = touch_contact_from_inbound(
                        workspace=event.workspace,
                        phone=normalized_phone,
                        full_name=profile_name,
                        extra={"wa_id": wa_contact_wa_id or wa_from},
                    )

                    msg_type = _map_msg_type(msg.get("type"))
                    body_text = _extract_body_text(msg)
                    msg_dt = _ts_to_dt(msg.get("timestamp"))

                    # ✅ Idempotent insert scoped by workspace + waba_message_id
                    ml, created = MessageLog.objects.get_or_create(
                        workspace=event.workspace,
                        waba_message_id=wa_msg_id,
                        defaults={
                            "direction": MessageDirection.INBOUND,
                            "msg_type": msg_type,
                            "status": MessageStatus.RECEIVED,
                            "contact": contact,
                            "contact_phone": normalized_phone,
                            "waba_phone_number_id": waba_phone_number_id,
                            "context_message_id": (msg.get("context") or {}).get("id"),
                            "body_text": body_text,
                            "payload": msg,
                            "received_at": msg_dt or timezone.now(),
                        },
                    )

                    # If duplicate webhook arrives, patch missing info safely
                    if not created:
                        updates: Dict[str, Any] = {}
                        if ml.contact_id is None and contact is not None:
                            updates["contact"] = contact
                        if not ml.body_text and body_text:
                            updates["body_text"] = body_text
                        if not ml.payload:
                            updates["payload"] = msg
                        if ml.received_at is None:
                            updates["received_at"] = msg_dt or timezone.now()

                        if updates:
                            for k, v in updates.items():
                                setattr(ml, k, v)
                            ml.save(update_fields=list(updates.keys()) + ["updated_at"])

                # 2) status updates (usually for outbound messages)
                statuses = value.get("statuses") or []
                for st in statuses:
                    wamid = st.get("id")
                    new_status = _map_meta_status(st.get("status"))

                    if not wamid or not new_status:
                        continue

                    st_dt = _ts_to_dt(st.get("timestamp"))

                    ml = (
                        MessageLog.objects.filter(
                            workspace=event.workspace,
                            waba_message_id=wamid,
                        ).first()
                    )
                    if not ml:
                        continue

                    updates: Dict[str, Any] = {}

                    # ✅ OUTBOUND: keep strict rank-based forward-only transitions
                    # ✅ INBOUND: allow DELIVERED/READ for testing (even if current is RECEIVED)
                    if ml.direction == MessageDirection.INBOUND:
                        if new_status in {MessageStatus.DELIVERED, MessageStatus.READ}:
                            updates["status"] = new_status
                        else:
                            continue
                    else:
                        # Only move status forward (avoid downgrades)
                        rank = {
                            MessageStatus.QUEUED: 0,
                            MessageStatus.SENT: 1,
                            MessageStatus.DELIVERED: 2,
                            MessageStatus.READ: 3,
                            MessageStatus.FAILED: 99,
                            # ⚠️ Don't let RECEIVED block outbound forward moves
                            MessageStatus.RECEIVED: 0,
                        }

                        if rank.get(new_status, 0) >= rank.get(ml.status, 0):
                            updates["status"] = new_status
                        else:
                            continue

                    if new_status == MessageStatus.SENT and ml.sent_at is None:
                        updates["sent_at"] = st_dt or timezone.now()

                    if new_status == MessageStatus.DELIVERED and ml.delivered_at is None:
                        updates["delivered_at"] = st_dt or timezone.now()

                    if new_status == MessageStatus.READ and ml.read_at is None:
                        updates["read_at"] = st_dt or timezone.now()

                    if new_status == MessageStatus.FAILED:
                        errs = st.get("errors") or []
                        if errs:
                            e0 = errs[0]
                            updates["error_code"] = str(e0.get("code") or "")
                            updates["error_message"] = e0.get("title") or e0.get("message") or ""

                    if updates:
                        for k, v in updates.items():
                            setattr(ml, k, v)
                        ml.save(update_fields=list(updates.keys()) + ["updated_at"])

        event.processing_status = WebhookProcessingStatus.PROCESSED
        event.processed_at = timezone.now()
        event.error_message = ""
        event.save(update_fields=["processing_status", "processed_at", "error_message", "updated_at"])

    except Exception as exc:  # noqa: BLE001
        logger.exception("Error processing webhook event %s: %s", event_id, exc)
        event.processing_status = WebhookProcessingStatus.FAILED
        event.error_message = str(exc)
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "error_message", "processed_at", "updated_at"])
        raise
