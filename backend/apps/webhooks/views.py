from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.whatsapp_accounts.models import WhatsappConnection
from .models import WebhookEventLog, WebhookProcessingStatus
from .tasks import process_webhook_event

logger = logging.getLogger(__name__)


def _extract_phone_number_id(payload: Dict[str, Any]) -> Optional[str]:
    """
    Meta Cloud API webhook commonly includes metadata.phone_number_id.
    """
    try:
        entry0 = (payload.get("entry") or [])[0]
        change0 = (entry0.get("changes") or [])[0]
        value = change0.get("value") or {}
        metadata = value.get("metadata") or {}
        return metadata.get("phone_number_id")
    except Exception:
        return None


def _compute_dedupe_key(payload: Dict[str, Any]) -> str:
    """
    Generate an idempotency key that is unique per *event type*.

    IMPORTANT:
    - Inbound message and status updates share the same wamid, so we must
      not dedupe them into one.
    """
    try:
        entry0 = (payload.get("entry") or [])[0]
        change0 = (entry0.get("changes") or [])[0]
        value = change0.get("value") or {}

        messages = value.get("messages") or []
        statuses = value.get("statuses") or []

        # 1) inbound message event
        if messages:
            mid = messages[0].get("id")
            if mid:
                return f"meta:msg:{mid}"

        # 2) status update event (include status + timestamp to allow multiple updates)
        if statuses:
            st0 = statuses[0] or {}
            sid = st0.get("id")
            sname = (st0.get("status") or "").lower()
            ts = st0.get("timestamp") or ""
            if sid:
                return f"meta:status:{sid}:{sname}:{ts}"

    except Exception:
        pass

    # fallback: stable hash of JSON
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "meta:hash:" + hashlib.sha256(blob).hexdigest()


def _is_valid_verify_token(token: Optional[str]) -> bool:
    """
    Accept verify token from either:
    - settings.META_VERIFY_TOKEN (global), OR
    - latest active WhatsappConnection.verify_token (DB)
    """
    if not token:
        return False

    # 1) Global token (optional)
    global_expected = getattr(settings, "META_VERIFY_TOKEN", None)
    if global_expected and token == global_expected:
        return True

    # 2) DB token (preferred for your current setup)
    try:
        conn = (
            WhatsappConnection.objects.filter(is_active=True)
            .order_by("-created_at")
            .only("verify_token")
            .first()
        )
        if conn and conn.verify_token and token == conn.verify_token:
            return True
    except Exception:
        logger.exception("Failed reading WhatsappConnection.verify_token for webhook verification")

    return False


class WhatsAppWebhookView(APIView):
    """
    Single ingress for WhatsApp Cloud API webhooks.

    GET: verify token challenge
    POST: store raw payload and enqueue Celery processing
    """
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        # Meta calls:
        # /webhooks/whatsapp/?hub.mode=subscribe&hub.challenge=123&hub.verify_token=XYZ
        if mode == "subscribe" and challenge and _is_valid_verify_token(token):
            logger.info("Webhook verification SUCCESS (mode=%s)", mode)
            return HttpResponse(challenge, content_type="text/plain", status=200)

        logger.warning(
            "Webhook verification FAILED mode=%s token=%s challenge_present=%s",
            mode,
            token,
            bool(challenge),
        )
        return HttpResponse("Verification failed", status=403, content_type="text/plain")

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        payload = request.data if isinstance(request.data, dict) else {}
        dedupe_key = _compute_dedupe_key(payload)

        phone_number_id = _extract_phone_number_id(payload)
        if not phone_number_id:
            ev = WebhookEventLog.objects.create(
                workspace=None,
                provider="META_WHATSAPP",
                phone_number_id="",
                dedupe_key=dedupe_key,
                payload=payload,
                processing_status=WebhookProcessingStatus.FAILED,
                error_message="Missing metadata.phone_number_id",
                request_headers=dict(request.headers),
                query_params=request.GET.dict(),
            )
            logger.warning("Webhook missing phone_number_id, event_id=%s", ev.id)
            return JsonResponse({"ok": True})

        conn = (
            WhatsappConnection.objects.filter(phone_number_id=phone_number_id)
            .select_related("workspace")
            .first()
        )
        if not conn:
            ev = WebhookEventLog.objects.create(
                workspace=None,
                provider="META_WHATSAPP",
                phone_number_id=phone_number_id,
                dedupe_key=dedupe_key,
                payload=payload,
                processing_status=WebhookProcessingStatus.FAILED,
                error_message=f"Unknown phone_number_id: {phone_number_id}",
                request_headers=dict(request.headers),
                query_params=request.GET.dict(),
            )
            logger.warning("Webhook for unknown phone_number_id=%s event_id=%s", phone_number_id, ev.id)
            return JsonResponse({"ok": True})

        # Dedupe at DB level for known workspace
        ev, created = WebhookEventLog.objects.get_or_create(
            workspace=conn.workspace,
            provider="META_WHATSAPP",
            dedupe_key=dedupe_key,
            defaults={
                "phone_number_id": phone_number_id,
                "payload": payload,
                "processing_status": WebhookProcessingStatus.PENDING,
                "request_headers": dict(request.headers),
                "query_params": request.GET.dict(),
            },
        )

        if created:
            process_webhook_event.delay(str(ev.id))

        return JsonResponse({"ok": True})
