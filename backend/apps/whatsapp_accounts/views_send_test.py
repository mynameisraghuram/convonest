# backend/apps/whatsapp_accounts/views_send_test.py

from __future__ import annotations

import re
import requests

from django.conf import settings
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # TODO: replace with IsAuthenticated later
from rest_framework.response import Response

from .models import WhatsappConnection

from apps.messaging.models import MessageLog  # ONLY import the model (no enums)


def _workspace_id_from_request(request):
    return request.headers.get("X-Workspace-Id") or request.query_params.get("workspace_id")


def _normalize_to_digits(to_raw: str) -> str:
    """
    WhatsApp Cloud API expects digits only for 'to' (no '+', no spaces).
    Example: +91 91603 81947 -> 919160381947
    """
    if not to_raw:
        return ""
    return re.sub(r"\D+", "", str(to_raw).strip())


@api_view(["POST"])
@permission_classes([AllowAny])  # TODO: make authenticated
def send_test_message(request):
    workspace_id = _workspace_id_from_request(request)
    to_raw = request.data.get("to")  # "919160381947" or "+91..."
    text = request.data.get("text") or "ConvoNest ✅ first real message"

    if not workspace_id:
        return Response({"detail": "workspace_id required"}, status=400)
    if not to_raw:
        return Response({"detail": "to required (e.g., 9198XXXXXXXX)"}, status=400)

    to_digits = _normalize_to_digits(to_raw)
    if len(to_digits) < 10:
        return Response({"detail": "Invalid 'to'. Use digits like 9198XXXXXXXXXX."}, status=400)

    conn = (
        WhatsappConnection.objects.select_related("phone_number")
        .filter(workspace_id=workspace_id, is_active=True)
        .order_by("-created_at")
        .first()
    )
    if not conn:
        return Response({"detail": "No active WhatsApp connection for this workspace"}, status=404)

    phone_number_id = str(getattr(conn, "phone_number_id", None) or conn.phone_number.id)
    token = conn.access_token

    url = f"{settings.META_API_BASE.rstrip('/')}/{phone_number_id}/messages"
    meta_payload = {
        "messaging_product": "whatsapp",
        "to": to_digits,
        "type": "text",
        "text": {"body": text},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1) Create MessageLog first (QUEUED)
    msg = MessageLog.objects.create(
        workspace_id=workspace_id,
        direction="OUT",
        status="QUEUED",
        msg_type="TEXT",
        contact_phone=f"+{to_digits}",
        body_text=text,
        waba_phone_number_id=str(phone_number_id),
        payload={
            "provider": "meta_whatsapp_cloud",
            "request": meta_payload,
        },
    )

    # 2) Call Meta
    try:
        r = requests.post(url, json=meta_payload, headers=headers, timeout=30)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
    except requests.RequestException as e:
        msg.status = "FAILED"
        msg.error_message = str(e)
        msg.payload = {**(msg.payload or {}), "exception": str(e)}
        msg.save(update_fields=["status", "error_message", "payload", "updated_at"])
        return Response({"detail": "Meta send failed (network)", "error": str(e), "message_log_id": msg.id}, status=400)

    # 3) Provider error
    if r.status_code >= 400:
        err = (data or {}).get("error") or {}
        msg.status = "FAILED"
        msg.error_code = str(err.get("code") or r.status_code)
        msg.error_message = err.get("message") or "Meta send failed"
        msg.payload = {**(msg.payload or {}), "response": data, "http_status": r.status_code}
        msg.save(update_fields=["status", "error_code", "error_message", "payload", "updated_at"])
        return Response({"detail": "Meta send failed", "meta": data, "message_log_id": msg.id}, status=400)

    # 4) Success: store wamid + mark SENT
    wamid = ""
    messages = (data or {}).get("messages") or []
    if isinstance(messages, list) and messages:
        wamid = messages[0].get("id") or ""

    msg.waba_message_id = wamid
    msg.status = "SENT"
    msg.sent_at = timezone.now()
    msg.payload = {**(msg.payload or {}), "response": data, "http_status": r.status_code}
    msg.save(update_fields=["waba_message_id", "status", "sent_at", "payload", "updated_at"])

    return Response(
        {"ok": True, "message_log_id": msg.id, "waba_message_id": wamid, "meta": data},
        status=200,
    )
