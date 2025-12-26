
#backend/apps/webhooks/views_whatsapp.py

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from apps.whatsapp_accounts.models import WhatsappConnection
from .models import WebhookEventLog, WebhookProcessingStatus
from .tasks import process_webhook_event
from .views import _compute_dedupe_key, _extract_phone_number_id

logger = logging.getLogger(__name__)


@csrf_exempt
def whatsapp_webhook(request):
    """
    WhatsApp Cloud API Webhook
    - GET  : Meta verification
    - POST : Incoming events (messages, statuses)
    """

    # -------------------------------------------------
    # 1) Meta Webhook Verification (GET)
    # -------------------------------------------------
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = (request.GET.get("hub.verify_token") or "").strip()
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == (getattr(settings, "META_VERIFY_TOKEN", "") or "").strip():
            return HttpResponse(challenge or "", status=200)

        return HttpResponse("Invalid verify token", status=403)

    # -------------------------------------------------
    # 2) Incoming Webhooks (POST)
    # -------------------------------------------------
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            payload = {}

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

    return HttpResponse("Method not allowed", status=405)
