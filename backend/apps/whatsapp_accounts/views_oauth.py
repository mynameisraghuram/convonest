# backend/apps/whatsapp_accounts/views_oauth.py

import secrets

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import WhatsappBusinessAccount, WhatsappPhoneNumber, WhatsappConnection

from .services_oauth import (
    build_oauth_state,
    parse_oauth_state,
    build_login_url,
    exchange_code_for_short_token,
    exchange_short_for_long_token,
    discover_waba_and_phone,
    subscribe_app_to_waba_webhooks,
)

# OPTIONAL (only if you want dev fallback)
try:
    from apps.workspaces.models import Workspace
except Exception:
    Workspace = None


def _workspace_id_from_request(request):
    # Header OR query param OR json body (POST)
    return (
        request.headers.get("X-Workspace-Id")
        or request.query_params.get("workspace_id")
        or (request.data.get("workspace_id") if isinstance(getattr(request, "data", None), dict) else None)
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def oauth_start(request):
    ws = _workspace_id_from_request(request)

    # Dev-friendly fallback: if you didn't pass workspace_id, use first workspace (ONLY in DEBUG)
    if not ws and settings.DEBUG and Workspace:
        first_ws = Workspace.objects.order_by("created_at").first()
        if first_ws:
            ws = str(first_ws.id)

    if not ws:
        return Response(
            {"detail": "workspace_id is required (send X-Workspace-Id header OR ?workspace_id=... OR POST body)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not settings.META_APP_ID or not settings.META_APP_SECRET or not settings.META_REDIRECT_URI:
        return Response({"detail": "Missing META_APP_ID / META_APP_SECRET / META_REDIRECT_URI"}, status=500)

    state = build_oauth_state(workspace_id=ws)
    auth_url = build_login_url(state=state)

    # If opened in browser, redirect. If called by API, return JSON.
    # Trigger redirect by either:
    #  - ?redirect=1
    #  - Accept: text/html (browser usually sends this)
    accept = (request.headers.get("Accept") or "").lower()
    wants_redirect = request.query_params.get("redirect") in ("1", "true", "yes") or "text/html" in accept

    if wants_redirect:
        return HttpResponseRedirect(auth_url)

    return Response({"auth_url": auth_url}) 


@api_view(["GET"])
@permission_classes([AllowAny])
def oauth_callback(request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        return Response({"detail": "Missing code/state"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        workspace_id = parse_oauth_state(state)["workspace_id"]
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    short = exchange_code_for_short_token(code)
    short_token = short.get("access_token")
    if not short_token:
        return Response({"detail": "No short-lived access token returned", "raw": short}, status=400)

    long = exchange_short_for_long_token(short_token)
    long_token = long.get("access_token")
    expires_in = long.get("expires_in")

    if not long_token:
        return Response({"detail": "No long-lived access token returned", "raw": long}, status=400)

    token_expires_at = None
    if expires_in:
        token_expires_at = timezone.now() + timezone.timedelta(seconds=int(expires_in))

    waba_id, phone_number_id, meta_discovery = discover_waba_and_phone(long_token)

    waba, _ = WhatsappBusinessAccount.objects.update_or_create(
        id=waba_id,
        defaults={"is_connected": True, "last_synced_at": timezone.now()},
    )

    phone, _ = WhatsappPhoneNumber.objects.update_or_create(
        id=phone_number_id,
        defaults={"waba": waba, "last_synced_at": timezone.now()},
    )

    # MVP rule: one active connection per workspace
    WhatsappConnection.objects.filter(workspace_id=workspace_id, is_active=True).update(is_active=False)

    verify_token = secrets.token_urlsafe(18)

    conn = WhatsappConnection.objects.create(
        workspace_id=workspace_id,
        waba=waba,
        phone_number=phone,
        access_token=long_token,
        token_expires_at=token_expires_at,
        verify_token=verify_token,
        scopes=list(getattr(settings, "META_OAUTH_SCOPES", [])),
        is_active=True,
    )

    subscribed = None
    try:
        subscribed = subscribe_app_to_waba_webhooks(long_token, waba_id)
    except Exception as e:
        subscribed = {"warning": str(e)}

    return Response(
        {
            "ok": True,
            "workspace_id": workspace_id,
            "connection_id": conn.id,
            "waba_id": waba_id,
            "phone_number_id": phone_number_id,
            "verify_token": verify_token,
            "subscribed_apps": subscribed,
            "meta_discovery": meta_discovery,
        },
        status=200,
    )
