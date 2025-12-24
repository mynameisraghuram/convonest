from __future__ import annotations
import logging
from typing import Any, Dict, Optional, Union

import requests
from django.conf import settings

from .models import (
    WhatsappBusinessAccount,
    WhatsappPhoneNumber,
    WhatsappQrCode,
    WhatsappConnection,
)

log = logging.getLogger(__name__)


def _api_url(path: str) -> str:
    # Prefer WHATSAPP_META API_BASE if present, else META_API_BASE
    base = None
    if hasattr(settings, "WHATSAPP_META") and settings.WHATSAPP_META.get("API_BASE"):
        base = settings.WHATSAPP_META["API_BASE"]
    elif hasattr(settings, "META_API_BASE") and settings.META_API_BASE:
        base = settings.META_API_BASE
    else:
        raise RuntimeError("Missing API base. Set WHATSAPP_META['API_BASE'] or META_API_BASE")

    base = base.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _get_active_connection(workspace_id: str) -> WhatsappConnection:
    conn = (
        WhatsappConnection.objects.select_related("waba", "phone_number", "workspace")
        .filter(workspace_id=workspace_id, is_active=True)
        .first()
    )
    if not conn:
        raise RuntimeError(f"No active WhatsApp connection for workspace_id={workspace_id}")
    return conn


def _headers_for_token(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _token_from_connection_or_settings(
    *,
    connection: Optional[WhatsappConnection] = None,
    workspace_id: Optional[str] = None,
) -> str:
    """
    Priority:
    1) explicit connection.access_token
    2) active connection by workspace_id
    3) legacy settings token (temporary fallback)
    """
    if connection and connection.access_token:
        return connection.access_token

    if workspace_id:
        conn = _get_active_connection(workspace_id)
        if conn.access_token:
            return conn.access_token

    # Legacy fallback (keep for now to avoid blocking dev)
    try:
        return settings.WHATSAPP_META["ACCESS_TOKEN"]
    except Exception:
        pass

    if hasattr(settings, "META_ACCESS_TOKEN"):
        return settings.META_ACCESS_TOKEN

    raise RuntimeError("No access token available (no connection token, no settings token).")


class WhatsappNumberService:
    @staticmethod
    def register_number(
        phone_number: WhatsappPhoneNumber,
        pin: str,
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> Dict[str, Any]:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{phone_number.id}/register")
        payload = {
            "messaging_product": "whatsapp",
            "pin": pin,
        }
        resp = requests.post(url, json=payload, headers=_headers_for_token(token), timeout=30)

        data = resp.json()
        if not resp.ok:
            log.error("Failed to register number: %s", data)
            raise Exception(f"Registration failed: {data}")

        phone_number.registered = True
        phone_number.save(update_fields=["registered"])
        return data

    @staticmethod
    def enable_two_step(
        phone_number: WhatsappPhoneNumber,
        pin: str,
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> Dict[str, Any]:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{phone_number.id}/two_step_verification")
        payload = {"pin": pin}
        resp = requests.post(url, json=payload, headers=_headers_for_token(token), timeout=30)

        data = resp.json()
        if not resp.ok:
            log.error("Failed to enable 2FA: %s", data)
            raise Exception(f"Two-step verification failed: {data}")

        phone_number.two_step_enabled = True
        phone_number.save(update_fields=["two_step_enabled"])
        return data

    @staticmethod
    def get_profile(
        phone_number: WhatsappPhoneNumber,
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> Dict[str, Any]:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{phone_number.id}/business_profile")
        resp = requests.get(url, headers=_headers_for_token(token), timeout=30)

        data = resp.json()
        if not resp.ok:
            log.error("Failed to fetch profile: %s", data)
            raise Exception(f"Profile fetch failed: {data}")

        phone_number.profile = data
        phone_number.save(update_fields=["profile"])
        return data

    @staticmethod
    def update_profile(
        phone_number: WhatsappPhoneNumber,
        fields: Dict[str, Any],
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> Dict[str, Any]:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{phone_number.id}/business_profile")
        resp = requests.post(url, json=fields, headers=_headers_for_token(token), timeout=30)

        data = resp.json()
        if not resp.ok:
            log.error("Failed to update profile: %s", data)
            raise Exception(f"Profile update failed: {data}")

        phone_number.profile = fields
        phone_number.save(update_fields=["profile"])
        return data


class WhatsappQrService:
    @staticmethod
    def create_qr(
        waba: WhatsappBusinessAccount,
        phone_number: WhatsappPhoneNumber,
        name: str,
        message: Optional[str] = None,
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> WhatsappQrCode:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{waba.id}/message_qrdls")
        payload: Dict[str, Any] = {
            "generate_qr_image": "PNG",
            "prefilled_message": message or "",
            "name": name,
            # NOTE: Some Graph versions expect phone_number_id instead of E164.
            # If QR creation fails, switch this to: "phone_number_id": phone_number.id
            "phone_number": phone_number.e164_number,
        }

        resp = requests.post(url, json=payload, headers=_headers_for_token(token), timeout=30)
        data = resp.json()

        if not resp.ok:
            log.error("Failed to create QR: %s", data)
            raise Exception(f"QR create failed: {data}")

        qr = WhatsappQrCode.objects.create(
            id=data["id"],
            waba=waba,
            phone_number=phone_number,
            name=name,
            deep_link=data.get("deep_link", ""),
            image_url=data.get("qr_image_url", ""),
            default_message=message or "",
            meta_raw=data,
        )
        return qr

    @staticmethod
    def sync_qrs(
        waba: WhatsappBusinessAccount,
        *,
        workspace_id: Optional[str] = None,
        connection: Optional[WhatsappConnection] = None,
    ) -> None:
        token = _token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)

        url = _api_url(f"{waba.id}/message_qrdls")
        resp = requests.get(url, headers=_headers_for_token(token), timeout=30)
        data = resp.json()

        if not resp.ok:
            log.error("Failed to list QR: %s", data)
            raise Exception(f"QR list failed: {data}")

        for item in data.get("data", []):
            pn = WhatsappPhoneNumber.objects.filter(
                waba=waba, e164_number=item.get("phone_number")
            ).first()
            if not pn:
                continue

            WhatsappQrCode.objects.update_or_create(
                id=item["id"],
                defaults={
                    "waba": waba,
                    "phone_number": pn,
                    "name": item.get("name", ""),
                    "deep_link": item.get("deep_link", ""),
                    "image_url": item.get("qr_image_url", ""),
                    "default_message": item.get("prefilled_message", ""),
                    "meta_raw": item,
                },
            )
